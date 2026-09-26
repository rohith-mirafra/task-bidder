import re
from datetime import datetime

from .extensions import db
from .models import TaskEligibility, User

# Recognizes one comma-separated segment of a required_skills string as a
# years-of-experience band instead of a plain skill tag - e.g. "5+ years",
# "3-5 yrs", "8+ years of experience". Anything that doesn't match this
# stays a plain skill tag, exactly as before.
_EXPERIENCE_PATTERN = re.compile(
    r"^(\d+)\s*(?:-\s*(\d+))?\s*\+?\s*(?:years?|yrs?)(?:\s+of\s+experience|\s+experience)?$",
    re.IGNORECASE,
)


def parse_skills(text):
    """Split a free-text, comma/semicolon-separated skills string into a
    normalized set of lowercase tags, e.g. "Python, AWS; react" -> {"python", "aws", "react"}."""
    if not text:
        return set()
    return {s.strip().lower() for s in text.replace(";", ",").split(",") if s.strip()}


def parse_requirement(text):
    """Split a required_skills string into (plain skill tags, min years,
    max years). At most one segment is treated as an experience band (the
    first one that matches); everything else - including a second band-like
    segment - is a plain skill tag. Returns (set[str], int|None, int|None)."""
    skills = set()
    min_years = None
    max_years = None
    if not text:
        return skills, min_years, max_years

    for segment in text.replace(";", ",").split(","):
        segment = segment.strip()
        if not segment:
            continue
        match = _EXPERIENCE_PATTERN.match(segment) if min_years is None else None
        if match:
            low = int(match.group(1))
            high = match.group(2)
            if high is not None:
                min_years, max_years = low, int(high)
            else:
                min_years = low
            continue
        skills.add(segment.lower())
    return skills, min_years, max_years


def _meets_experience(worker_years, min_years, max_years):
    if min_years is not None and worker_years < min_years:
        return False
    if max_years is not None and worker_years > max_years:
        return False
    return True


def refresh_task_eligibility(task, now=None):
    """Recompute and persist which current workers satisfy task's
    required_skills - both the plain skill tags and, if present, the
    years-of-experience band - replacing any prior snapshot. No-op if the
    task has no skill requirement. Caller commits - this only stages the
    changes, so a bulk refresh across many tasks can commit once at the end."""
    if not task.has_skill_requirement:
        return

    required_skills, min_years, max_years = parse_requirement(task.required_skills)
    TaskEligibility.query.filter_by(task_id=task.id).delete()

    now = now or datetime.utcnow()
    for worker in User.query.filter_by(role="worker").all():
        if not required_skills.issubset(parse_skills(worker.skills)):
            continue
        if not _meets_experience(worker.experience, min_years, max_years):
            continue
        db.session.add(TaskEligibility(task_id=task.id, user_id=worker.id, computed_at=now))

    task.eligibility_computed_at = now
