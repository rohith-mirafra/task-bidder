"""Seed initial users. Edit SEED_USERS with real names before running,
then have each person change their password after first login (a
self-service password change isn't built yet - see README follow-ups)."""

from app import create_app
from app.extensions import db
from app.models import User

# (username, display_name, role, password)
SEED_USERS = [
    ("creator1", "Creator One", "creator", "changeme123"),
    ("creator2", "Creator Two", "creator", "changeme123"),
    ("creator3", "Creator Three", "creator", "changeme123"),
    ("creator4", "Creator Four", "creator", "changeme123"),
    ("worker1", "Worker One", "worker", "changeme123"),
    ("worker2", "Worker Two", "worker", "changeme123"),
    ("worker3", "Worker Three", "worker", "changeme123"),
    ("worker4", "Worker Four", "worker", "changeme123"),
    ("worker5", "Worker Five", "worker", "changeme123"),
    ("worker6", "Worker Six", "worker", "changeme123"),
]


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        created = 0
        for username, display_name, role, password in SEED_USERS:
            if User.query.filter_by(username=username).first():
                continue
            user = User(username=username, display_name=display_name, role=role)
            user.set_password(password)
            db.session.add(user)
            created += 1
        db.session.commit()
        print(f"Created {created} new user(s). Total users: {User.query.count()}")


if __name__ == "__main__":
    main()
