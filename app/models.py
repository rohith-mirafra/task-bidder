from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'creator' or 'worker'
    skills = db.Column(db.Text, default="")  # worker capabilities, free text e.g. "python, aws"
    # Independent of role - a status any user can carry, not a third role.
    # Lets someone be a creator (or worker) *and* an admin on one account,
    # and there can be more than one admin at a time.
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_creator(self):
        return self.role == "creator"

    @property
    def is_worker(self):
        return self.role == "worker"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default="")
    points = db.Column(db.Integer, nullable=False, default=1)
    priority = db.Column(db.String(10), nullable=False, default="medium")  # low/medium/high
    deadline = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(15), nullable=False, default="open")
    # open -> claimed -> in_progress -> done

    # Free-text, set once by the creator (e.g. "python, aws, react"). Blank
    # means the task is open to every worker with no skill gating.
    required_skills = db.Column(db.Text, default="")
    # Set each time an admin (re-)runs the selection below. Null means the
    # selection has never been run for this task yet.
    eligibility_computed_at = db.Column(db.DateTime, nullable=True)

    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    claimed_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    owner = db.relationship("User", foreign_keys=[owner_id])
    assignee = db.relationship("User", foreign_keys=[assignee_id])

    @property
    def has_skill_requirement(self):
        return bool((self.required_skills or "").strip())

    def is_worker_eligible(self, user_id):
        """Whether a worker may claim this task. Tasks with no skill
        requirement are open to everyone; otherwise the worker must appear
        in the eligibility snapshot from the last admin-triggered selection."""
        if not self.has_skill_requirement:
            return True
        return any(row.user_id == user_id for row in self.eligibility_rows)

    def eligible_worker_ids(self):
        return {row.user_id for row in self.eligibility_rows}


class TaskEligibility(db.Model):
    """A snapshot row: worker `user_id` matched task `task_id`'s required
    skills the last time an admin ran the selection. Recomputed (deleted and
    reinserted) from scratch on every run rather than kept live, since the
    worker pool and their skills change independently of any given task."""

    __tablename__ = "task_eligibility"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    computed_at = db.Column(db.DateTime, default=datetime.utcnow)

    task = db.relationship("Task", backref="eligibility_rows")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("task_id", "user_id", name="uq_task_worker_eligibility"),
    )
