from datetime import date, datetime

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .extensions import db
from .models import Task, TaskEligibility, User
from .notifications import notify_new_task, notify_task_claimed, notify_task_submitted_for_review
from .utils import refresh_task_eligibility

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

    if current_user.is_worker:
        # Tasks are shown only to workers currently eligible for them - a
        # worker never sees a task they can't claim just by browsing. The
        # one exception is a task they're already assigned to: eligibility
        # can drift after they claim it (the pool keeps changing), but work
        # already in progress must never disappear from their own board.
        eligible_task_ids = db.session.query(TaskEligibility.task_id).filter(
            TaskEligibility.user_id == current_user.id
        )
        query = query.filter(
            db.or_(Task.assignee_id == current_user.id, Task.id.in_(eligible_task_ids))
        )

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
        if not required_skills:
            abort(400)

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
        # Eligibility is derived from required_skills the moment the task
        # exists, so the board and the notification both reflect the
        # current worker pool from the start - an admin's global refresh
        # later only matters once that pool has moved on.
        refresh_task_eligibility(task)
        db.session.commit()
        notify_new_task(task)
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
    notify_task_claimed(task)
    return _render_row(task)


@bp.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def update_status(task_id):
    task = Task.query.get_or_404(task_id)
    if task.assignee_id != current_user.id:
        abort(403)

    new_status = request.form.get("new_status")
    # A worker can carry a task up to pending_review - only the task's own
    # creator can move it from there into done (or send it back).
    allowed_transitions = {"claimed": "in_progress", "in_progress": "pending_review"}
    if allowed_transitions.get(task.status) != new_status:
        abort(400)

    task.status = new_status
    db.session.commit()
    if new_status == "pending_review":
        notify_task_submitted_for_review(task)
    return _render_row(task)


@bp.route("/tasks/<int:task_id>/review", methods=["POST"])
@login_required
def review_task(task_id):
    task = Task.query.get_or_404(task_id)
    # Deliberately narrower than reassignment: only the task's own creator
    # vets it, not any creator.
    if not current_user.is_creator or task.owner_id != current_user.id:
        abort(403)
    if task.status != "pending_review":
        abort(400)

    decision = request.form.get("decision")
    if decision == "approve":
        task.status = "done"
        task.completed_at = datetime.utcnow()
    elif decision == "reject":
        task.status = "in_progress"
    else:
        abort(400)

    db.session.commit()
    return _render_row(task)


@bp.route("/tasks/<int:task_id>/edit-skills", methods=["POST"])
@login_required
def edit_skills(task_id):
    task = Task.query.get_or_404(task_id)
    if not current_user.is_admin or task.status == "done":
        abort(403)

    required_skills = request.form.get("required_skills", "").strip()
    if not required_skills:
        abort(400)

    task.required_skills = required_skills
    db.session.commit()
    # Criteria just changed, so the old snapshot no longer means anything -
    # this always recomputes, independent of the admin's global refresh.
    refresh_task_eligibility(task)
    db.session.commit()
    return _render_row(task)


@bp.route("/tasks/<int:task_id>/reassign", methods=["POST"])
@login_required
def reassign_task(task_id):
    task = Task.query.get_or_404(task_id)
    # Admin holds this override too, even on an account that isn't also a
    # creator - "editing the filter criteria or overriding a W's bid" is
    # explicitly an admin power, not just a creator one.
    if not (current_user.is_creator or current_user.is_admin) or task.status == "done":
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
