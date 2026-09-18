from datetime import datetime

from .extensions import db
from .models import TaskEligibility, User


def parse_skills(text):
    """Split a free-text, comma/semicolon-separated skills string into a
    normalized set of lowercase tags, e.g. "Python, AWS; react" -> {"python", "aws", "react"}."""
    if not text:
        return set()
    return {s.strip().lower() for s in text.replace(";", ",").split(",") if s.strip()}


def refresh_task_eligibility(task, now=None):
    """Recompute and persist which current workers satisfy task's
    required_skills, replacing any prior snapshot. No-op if the task has no
    skill requirement. Caller commits - this only stages the changes, so a
    bulk refresh across many tasks can commit once at the end."""
    if not task.has_skill_requirement:
        return

    required = parse_skills(task.required_skills)
    TaskEligibility.query.filter_by(task_id=task.id).delete()

    now = now or datetime.utcnow()
    for worker in User.query.filter_by(role="worker").all():
        if required.issubset(parse_skills(worker.skills)):
            db.session.add(TaskEligibility(task_id=task.id, user_id=worker.id, computed_at=now))

    task.eligibility_computed_at = now
