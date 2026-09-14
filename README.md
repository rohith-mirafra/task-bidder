# Task Bidder

A small internal tool for a creator team (C) to post tasks and a worker team (W)
to claim, work, and complete them for points. Everyone shares the same task
board and leaderboard view; permissions differ by role, not by page.

## How it works

- **Creators** create tasks (title, description, points, priority, deadline).
- **Workers** claim any `open` task on a first-come basis. Claiming assigns it
  to them and moves it to `claimed`.
- The assignee moves their own task forward: `claimed` -> `in_progress` -> `done`.
- Once a task is claimed, only a **creator** can reassign it to someone else
  or send it back to `open` (workers cannot hand off or unclaim it themselves).
- Everyone can filter the task list by owner (creator) and by assignee (worker).
- The leaderboard sums points from `done` tasks per worker.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Edit `seed.py` to list your real creators and workers (usernames, display
names, roles), then run it once to create the database and accounts:

```bash
python seed.py
```

Everyone is seeded with the password `changeme123` — there's no self-service
password change yet (see Follow-ups), so tell people to treat it as a shared
placeholder for now, or edit `seed.py` to set distinct passwords per person.

Run the app:

```bash
python run.py
```

Visit http://localhost:5000 and log in.

## Project layout

```
app/
  __init__.py       app factory
  extensions.py     db, login_manager
  models.py         User, Task
  auth.py           login/logout routes
  tasks.py          task board, claim/status/reassign, leaderboard
  templates/        Jinja templates (+ htmx partial for task rows)
  static/style.css
seed.py             one-off script to create user accounts
run.py              dev server entrypoint
config.py           SECRET_KEY / DB URL, overridable via env vars
```

Data lives in a single SQLite file (`taskbidder.db`), created automatically.

## Follow-ups (not built yet, deliberately out of scope for v1)

- Self-service password change / admin user management UI.
- MS Teams notification when a new task opens for bidding (incoming webhook
  is the simplest next step).
- Points-based bidding/auction instead of first-come claiming.
- Badges / streaks beyond the raw points leaderboard.
