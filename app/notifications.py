import logging
import os

import requests
from flask import current_app

logger = logging.getLogger(__name__)


def _load_urls(config_key):
    """Read Teams Incoming Webhook URLs from an admin-maintained text file,
    one per line. Re-read on every call (not cached) so an admin's edit takes
    effect immediately without restarting the app. Blank lines and lines
    starting with # are ignored."""
    path = current_app.config[config_key]
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]


def _load_worker_webhook_map():
    """Read the admin-maintained "username,webhook_url" mapping - one worker
    per line - so a new task can be pushed only to the workers who are
    currently eligible for it, not broadcast to everyone. Re-read on every
    call for the same reason as _load_urls."""
    path = current_app.config["TEAMS_WORKER_WEBHOOKS_FILE"]
    if not os.path.exists(path):
        return {}
    mapping = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "," not in line:
                continue
            username, url = line.split(",", 1)
            username, url = username.strip(), url.strip()
            if username and url:
                mapping[username] = url
    return mapping


def _fanout(urls, payload):
    """Best-effort fan-out to every given webhook URL. Never raises - a
    Teams outage or a stale URL in the file must not break the request that
    triggered the notification, so failures are logged and otherwise
    swallowed."""
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


def _task_board_link():
    app_base_url = current_app.config.get("APP_BASE_URL")
    if not app_base_url:
        return None
    return {
        "@type": "OpenUri",
        "name": "View task board",
        "targets": [{"os": "default", "uri": f"{app_base_url.rstrip('/')}/tasks"}],
    }


def _card(title, text, facts):
    card = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title,
        "themeColor": "4F46E5",
        "title": title,
        "text": text,
        "sections": [{"facts": facts}],
    }
    link = _task_board_link()
    if link:
        card["potentialAction"] = [link]
    return card


def notify_new_task(task):
    """New task posted, open for bidding. Unlike the other two events, this
    does NOT broadcast: it goes only to workers currently in the task's
    eligibility snapshot (computed moments earlier at creation), looked up
    by username in the admin-maintained worker webhook map. A worker with
    no entry in that map is silently skipped - nothing to notify them with."""
    worker_map = _load_worker_webhook_map()
    if not worker_map:
        return

    eligible_usernames = {row.user.username for row in task.eligibility_rows}
    urls = [worker_map[username] for username in eligible_usernames if username in worker_map]
    if not urls:
        return

    facts = [
        {"name": "Points", "value": str(task.points)},
        {"name": "Priority", "value": task.priority},
        {"name": "Created by", "value": task.owner.display_name},
        {"name": "Requires", "value": task.required_skills},
    ]
    if task.deadline:
        facts.append({"name": "Deadline", "value": task.deadline.strftime("%Y-%m-%d")})

    title = f"New task open for bidding: {task.title}"
    _fanout(urls, _card(title, task.description or "", facts))


def notify_task_claimed(task):
    """A worker picked up a task. Fans out to the C-group's
    teams_webhooks_creators.txt so every creator hears about it, not just
    the task's own owner."""
    urls = _load_urls("TEAMS_CREATOR_WEBHOOKS_FILE")
    if not urls:
        return

    title = f"Task claimed: {task.title}"
    text = f"{task.assignee.display_name} picked up this task."
    facts = [
        {"name": "Claimed by", "value": task.assignee.display_name},
        {"name": "Points", "value": str(task.points)},
        {"name": "Created by", "value": task.owner.display_name},
    ]
    _fanout(urls, _card(title, text, facts))


def notify_task_submitted_for_review(task):
    """A worker marked their task done (submitted it for review). Fans out
    to the C-group's teams_webhooks_creators.txt - the owning creator still
    has to approve it in the app, but every creator is told right away."""
    urls = _load_urls("TEAMS_CREATOR_WEBHOOKS_FILE")
    if not urls:
        return

    title = f"Task marked done, needs review: {task.title}"
    text = f"{task.assignee.display_name} marked this task as done."
    facts = [
        {"name": "Marked done by", "value": task.assignee.display_name},
        {"name": "Owner (approves it)", "value": task.owner.display_name},
        {"name": "Points", "value": str(task.points)},
    ]
    _fanout(urls, _card(title, text, facts))
