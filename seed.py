"""Seed initial users. Edit SEED_USERS with real names before running,
then have each person change their password after first login (a
self-service password change isn't built yet - see README follow-ups)."""

from app import create_app
from app.extensions import db
from app.models import User

# (username, display_name, role, password, skills, experience, is_admin)
# skills and experience only matter for role="worker" - skills is
# comma-separated free text; experience is years, compared against a
# years-of-experience band that may appear in a task's required_skills
# (e.g. "5+ years"). is_admin is independent of role - any user can carry
# it, and more than one person can hold it at once (here, two of the
# creators do).
SEED_USERS = [
    ("creator1", "Creator One", "creator", "changeme123", "", 0, True),
    ("creator2", "Creator Two", "creator", "changeme123", "", 0, True),
    ("creator3", "Creator Three", "creator", "changeme123", "", 0, False),
    ("creator4", "Creator Four", "creator", "changeme123", "", 0, False),
    ("worker1", "Worker One", "worker", "changeme123", "python, sql", 3, False),
    ("worker2", "Worker Two", "worker", "changeme123", "react, javascript", 2, False),
    ("worker3", "Worker Three", "worker", "changeme123", "python, aws", 5, False),
    ("worker4", "Worker Four", "worker", "changeme123", "java, sql", 4, False),
    ("worker5", "Worker Five", "worker", "changeme123", "react, css", 1, False),
    ("worker6", "Worker Six", "worker", "changeme123", "python, react", 6, False),
]


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        created = 0
        for username, display_name, role, password, skills, experience, is_admin in SEED_USERS:
            if User.query.filter_by(username=username).first():
                continue
            user = User(
                username=username,
                display_name=display_name,
                role=role,
                skills=skills,
                experience=experience,
                is_admin=is_admin,
            )
            user.set_password(password)
            db.session.add(user)
            created += 1
        db.session.commit()
        print(f"Created {created} new user(s). Total users: {User.query.count()}")


if __name__ == "__main__":
    main()
