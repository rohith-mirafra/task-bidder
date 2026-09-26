import os

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .extensions import db
from .models import Task, User
from .utils import refresh_task_eligibility

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_admin():
    if not current_user.is_admin:
        abort(403)


def _parse_experience(raw):
    """Non-negative integer years, defaulting to 0 for a blank value.
    Raises ValueError for anything else invalid - callers decide whether
    that means abort(400) or "invalid row"."""
    raw = (raw or "").strip()
    if not raw:
        return 0
    value = int(raw)  # raises ValueError for non-numeric input
    if value < 0:
        raise ValueError("experience must be non-negative")
    return value


@bp.route("/workers")
@login_required
def list_workers():
    _require_admin()
    workers = User.query.filter_by(role="worker").order_by(User.display_name).all()
    return render_template("workers.html", workers=workers)


@bp.route("/workers/<int:user_id>", methods=["POST"])
@login_required
def update_worker(user_id):
    _require_admin()
    worker = User.query.filter_by(id=user_id, role="worker").first_or_404()
    try:
        experience = _parse_experience(request.form.get("experience"))
    except ValueError:
        abort(400)
    worker.skills = request.form.get("skills", "").strip()
    worker.experience = experience
    db.session.commit()
    return redirect(url_for("admin.list_workers"))


@bp.route("/workers/new", methods=["POST"])
@login_required
def new_worker():
    _require_admin()
    username = request.form.get("username", "").strip()
    display_name = request.form.get("display_name", "").strip()
    password = request.form.get("password", "").strip()
    skills = request.form.get("skills", "").strip()
    try:
        experience = _parse_experience(request.form.get("experience"))
    except ValueError:
        abort(400)

    if not username or not display_name or not password:
        abort(400)
    if User.query.filter_by(username=username).first():
        abort(400)

    worker = User(
        username=username,
        display_name=display_name,
        role="worker",
        skills=skills,
        experience=experience,
    )
    worker.set_password(password)
    db.session.add(worker)
    db.session.commit()
    return redirect(url_for("admin.list_workers"))


@bp.route("/workers/bulk-import", methods=["POST"])
@login_required
def bulk_import_workers():
    _require_admin()
    # Same convention as the Teams webhook files: an admin-maintained text
    # file edited directly on the server, not uploaded through the browser.
    path = current_app.config["BULK_WORKERS_FILE"]
    if not os.path.exists(path):
        flash(f"No bulk import file found at {path}.")
        return redirect(url_for("admin.list_workers"))

    created = skipped = invalid = 0
    with open(path) as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # username,display_name,password,experience,skills - skills may
            # itself contain commas, so only the first 4 commas are field
            # separators; everything after that is the skills string as-is.
            parts = line.split(",", 4)
            username = parts[0].strip() if len(parts) > 0 else ""
            display_name = parts[1].strip() if len(parts) > 1 else ""
            password = parts[2].strip() if len(parts) > 2 else ""
            experience_raw = parts[3] if len(parts) > 3 else ""
            skills = parts[4].strip() if len(parts) > 4 else ""

            if not username or not display_name or not password:
                invalid += 1
                continue
            try:
                experience = _parse_experience(experience_raw)
            except ValueError:
                invalid += 1
                continue
            if User.query.filter_by(username=username).first():
                skipped += 1
                continue

            worker = User(
                username=username,
                display_name=display_name,
                role="worker",
                skills=skills,
                experience=experience,
            )
            worker.set_password(password)
            db.session.add(worker)
            created += 1

    db.session.commit()
    flash(f"Bulk import: {created} created, {skipped} skipped (username already exists), {invalid} invalid row(s).")
    return redirect(url_for("admin.list_workers"))


@bp.route("/refresh-eligibility", methods=["POST"])
@login_required
def refresh_eligibility():
    _require_admin()
    # One global trigger, not a per-task button: the worker pool is what
    # actually changes (new workers, edited skills), so a single pass
    # recomputes every task that has a skill requirement and isn't done yet.
    tasks = [t for t in Task.query.filter(Task.status != "done").all() if t.has_skill_requirement]
    for task in tasks:
        refresh_task_eligibility(task)
    db.session.commit()
    flash(f"Refreshed eligibility for {len(tasks)} task(s).")
    return redirect(url_for("admin.list_workers"))
