import logging
import os

import requests
from flask import current_app

logger = logging.getLogger(__name__)


def _load_webhook_urls():
    """Read Teams Incoming Webhook URLs from the admin-maintained text file,
    one per line. Re-read on every call (not cached) so an admin's edit takes
    effect immediately without restarting the app. Blank lines and lines
    starting with # are ignored."""
    path = current_app.config["TEAMS_WEBHOOKS_FILE"]
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]


def _build_message_card(task):
    facts = [
        {"name": "Points", "value": str(task.points)},
        {"name": "Priority", "value": task.priority},
        {"name": "Created by", "value": task.owner.display_name},
    ]
    if task.deadline:
        facts.append({"name": "Deadline", "value": task.deadline.strftime("%Y-%m-%d")})
    if task.has_skill_requirement:
        facts.append({"name": "Requires", "value": task.required_skills})

    card = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": f"New task open for bidding: {task.title}",
        "themeColor": "4F46E5",
        "title": f"New task open for bidding: {task.title}",
        "text": task.description or "",
        "sections": [{"facts": facts}],
    }

    app_base_url = current_app.config.get("APP_BASE_URL")
    if app_base_url:
        card["potentialAction"] = [
            {
                "@type": "OpenUri",
                "name": "View task board",
                "targets": [{"os": "default", "uri": f"{app_base_url.rstrip('/')}/tasks"}],
            }
        ]
    return card


def notify_new_task(task):
    """Best-effort fan-out to every webhook in the admin-maintained list.
    Never raises - a Teams outage or a stale URL in the file must not break
    task creation, so failures are logged and otherwise swallowed."""
    urls = _load_webhook_urls()
    if not urls:
        return

    payload = _build_message_card(task)
    for url in urls:
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code >= 300:
                logger.warning(
                    "Teams webhook notification failed (status %s) for %s",
                    response.status_code,
                    url,
                )
        except requests.RequestException:
            logger.warning("Teams webhook notification errored for %s", url, exc_info=True)
