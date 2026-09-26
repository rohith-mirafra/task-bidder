import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'taskbidder.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # "username,webhook_url" per line, one per worker, maintained directly by
    # admins (not through the web UI). New-task notifications look up only
    # the currently-eligible workers here - see teams_webhooks_workers.txt.example.
    TEAMS_WORKER_WEBHOOKS_FILE = os.environ.get(
        "TEAMS_WORKER_WEBHOOKS_FILE", os.path.join(basedir, "teams_webhooks_workers.txt")
    )
    # Flat list of webhook URLs, one per line: where the C group hears "task
    # claimed" and "task submitted for review" notifications (broadcast to
    # everyone on the list, not filtered). See teams_webhooks_creators.txt.example.
    TEAMS_CREATOR_WEBHOOKS_FILE = os.environ.get(
        "TEAMS_CREATOR_WEBHOOKS_FILE", os.path.join(basedir, "teams_webhooks_creators.txt")
    )
    # Used to build a "View task board" link in Teams notifications. Leave
    # unset while running locally - the link is simply omitted.
    APP_BASE_URL = os.environ.get("APP_BASE_URL")

    # "username,display_name,password,skills" per line - an admin drops
    # workers here and clicks Import on the Workers page. Not through the
    # web UI itself (no file upload) - see bulk_workers.txt.example.
    BULK_WORKERS_FILE = os.environ.get(
        "BULK_WORKERS_FILE", os.path.join(basedir, "bulk_workers.txt")
    )
