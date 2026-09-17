from datetime import date, datetime

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .extensions import db
from .models import Task, TaskEligibility, User
from .utils import parse_skills

bp = Blueprint("tasks", __name__)


def _creators_and_workers():
    creators = User.query.filter_by(role="creator").order_by(User.display_name).all()
    workers = User.query.filter_by(role="worker").order_by(User.display_name).all()
    return creators, workers


def _render_row(task):
    _, workers = _creators_and_workers()
    return render_template("partials/_task_row.html", task=task, workers=workers)


@bp.route("/")
@login_required
def index():
    return redirect(url_for("tasks.list_tasks"))


@bp.route("/tasks")
@login_required
def list_tasks():
    query = Task.query

    owner_id = request.args.get("owner_id")
    assignee_id = request.args.get("assignee_id")
    status = request.args.get("status")

    if owner_id:
        query = query.filter(Task.owner_id == int(owner_id))
    if assignee_id == "unassigned":
        query = query.filter(Task.assignee_id.is_(None))
    elif assignee_id:
        query = query.filter(Task.assignee_id == int(assignee_id))
    if status:
        query = query.filter(Task.status == status)

    tasks = query.order_by(Task.created_at.desc()).all()
    creators, workers = _creators_and_workers()
    return render_template("tasks.html", tasks=tasks, creators=creators, workers=workers)


@bp.route("/tasks/new", methods=["GET", "POST"])
@login_required
def new_task():
    if not current_user.is_creator:
        abort(403)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            abort(400)

        description = request.form.get("description", "").strip()
        points = max(1, int(request.form.get("points") or 1))
        priority = request.form.get("priority", "medium")
        if priority not in ("low", "medium", "high"):
            priority = "medium"

        deadline_str = request.form.get("deadline")
        deadline = date.fromisoformat(deadline_str) if deadline_str else None
        required_skills = request.form.get("required_skills", "").strip()

        task = Task(
            title=title,
            description=description,
            points=points,
            priority=priority,
            deadline=deadline,
            required_skills=required_skills,
            owner_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()
        return redirect(url_for("tasks.list_tasks"))

    return render_template("new_task.html")


@bp.route("/tasks/<int:task_id>/claim", methods=["POST"])
@login_required
def claim_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not current_user.is_worker or task.status != "open":
        abort(403)
    if not task.is_worker_eligible(current_user.id):
        abort(403)

    task.assignee_id = current_user.id
    task.status = "claimed"
    task.claimed_at = datetime.utcnow()
    db.session.commit()
    return _render_row(task)


@bp.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def update_status(task_id):
    task = Task.query.get_or_404(task_id)
    if task.assignee_id != current_user.id:
        abort(403)

    new_status = request.form.get("new_status")
    allowed_transitions = {"claimed": "in_progress", "in_progress": "done"}
    if allowed_transitions.get(task.status) != new_status:
        abort(400)

    task.status = new_status
    if new_status == "done":
        task.completed_at = datetime.utcnow()
    db.session.commit()
    return _render_row(task)


@bp.route("/tasks/<int:task_id>/reassign", methods=["POST"])
@login_required
def reassign_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not current_user.is_creator or task.status == "done":
        abort(403)

    assignee_id = request.form.get("assignee_id")
    if assignee_id:
        worker = User.query.filter_by(id=int(assignee_id), role="worker").first_or_404()
        task.assignee_id = worker.id
        task.status = "claimed"
        task.claimed_at = datetime.utcnow()
    else:
        task.assignee_id = None
        task.status = "open"
        task.claimed_at = None

    db.session.commit()
    return _render_row(task)


@bp.route("/tasks/<int:task_id>/run-selection", methods=["POST"])
@login_required
def run_selection(task_id):
    task = Task.query.get_or_404(task_id)
    if not current_user.is_admin:
        abort(403)

    required = parse_skills(task.required_skills)
    TaskEligibility.query.filter_by(task_id=task.id).delete()

    now = datetime.utcnow()
    if required:
        for worker in User.query.filter_by(role="worker").all():
            if required.issubset(parse_skills(worker.skills)):
                db.session.add(TaskEligibility(task_id=task.id, user_id=worker.id, computed_at=now))

    task.eligibility_computed_at = now
    db.session.commit()
    return _render_row(task)


@bp.route("/leaderboard")
@login_required
def leaderboard():
    rows = (
        db.session.query(
            User,
            db.func.coalesce(db.func.sum(Task.points), 0).label("total_points"),
            db.func.count(Task.id).label("tasks_done"),
        )
        .outerjoin(Task, db.and_(Task.assignee_id == User.id, Task.status == "done"))
        .filter(User.role == "worker")
        .group_by(User.id)
        .order_by(db.desc("total_points"))
        .all()
    )
    return render_template("leaderboard.html", rows=rows)
