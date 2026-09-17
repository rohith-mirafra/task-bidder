import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'taskbidder.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Plain text file, one MS Teams Incoming Webhook URL per line, maintained
    # directly by admins (not through the web UI). See teams_webhooks.txt.example.
    TEAMS_WEBHOOKS_FILE = os.environ.get(
        "TEAMS_WEBHOOKS_FILE", os.path.join(basedir, "teams_webhooks.txt")
    )
    # Used to build a "View task board" link in Teams notifications. Leave
    # unset while running locally - the link is simply omitted.
    APP_BASE_URL = os.environ.get("APP_BASE_URL")
