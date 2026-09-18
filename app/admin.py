from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .extensions import db
from .models import Task, User
from .utils import refresh_task_eligibility

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_admin():
    if not current_user.is_admin:
        abort(403)


@bp.route("/workers")
@login_required
def list_workers():
    _require_admin()
    workers = User.query.filter_by(role="worker").order_by(User.display_name).all()
    return render_template("workers.html", workers=workers)


@bp.route("/workers/<int:user_id>/skills", methods=["POST"])
@login_required
def update_skills(user_id):
    _require_admin()
    worker = User.query.filter_by(id=user_id, role="worker").first_or_404()
    worker.skills = request.form.get("skills", "").strip()
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

    if not username or not display_name or not password:
        abort(400)
    if User.query.filter_by(username=username).first():
        abort(400)

    worker = User(username=username, display_name=display_name, role="worker", skills=skills)
    worker.set_password(password)
    db.session.add(worker)
    db.session.commit()
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
