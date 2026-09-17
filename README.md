# Task Bidder

A small internal tool for a creator team (C) to post tasks and a worker team (W)
to claim, work, and complete them for points. Everyone shares the same task
board and leaderboard view; permissions differ by role, not by page.

## How it works

- **Creators** create tasks (title, description, points, priority, deadline,
  and optionally a required-skills string).
- **Workers** claim any `open` task they're eligible for on a first-come
  basis. Claiming assigns it to them and moves it to `claimed`.
- The assignee moves their own task forward: `claimed` -> `in_progress` -> `done`.
- Once a task is claimed, only a **creator** can reassign it to someone else
  or send it back to `open` (workers cannot hand off or unclaim it themselves).
  Reassignment is a manual creator override and ignores skill eligibility.
- Everyone can filter the task list by owner (creator) and by assignee (worker).
- The leaderboard sums points from `done` tasks per worker.

## Worker selection by skill (per task)

The worker pool (W) is larger than any one task needs and keeps growing, so
each task can restrict who's allowed to claim it:

- Each task's creator sets `required_skills` once, at task creation - free
  text, comma-separated (e.g. `python, aws`). Leave it blank and the task
  stays open to every worker, exactly as before. Only that task's creator
  sets it, and only for that task - it isn't an admin power.
- Each worker has a `skills` field (also free text, comma-separated),
  managed on the **Workers** page (visible to admins only).
- Matching is "worker has all of the task's required skills" - not live. An
  **admin** must click **Run selection** on a task to (re-)compute which
  current workers qualify. That snapshot (who's eligible, and when it was
  computed) is what actually gates the Claim button - it does not
  auto-update as the worker pool or their skills change, by design, since
  re-running is an explicit, admin-triggered action.
- The task row shows the requirement, the eligible worker count, and the
  last-run timestamp (or "selection not run yet" if it's never been run -
  in that case nobody can claim a skill-gated task until an admin runs it).

`admin` is a status (`User.is_admin`), not a third role - it's independent
of `role` (`creator`/`worker`), more than one person can hold it, and a
creator can also be an admin on the same account (seed data gives two of
the four seeded creators the flag as an example). Admin only gates the
worker-skills page and running selection; it grants no extra power over
creating tasks or setting a task's own required skills - that's still
strictly the task's creator, on their own tasks only.

This is a skeleton: matching is a simple set-membership check (no fuzzy
matching, synonyms, or weighting).

## MS Teams notification on new tasks

When a creator posts a new task, the app pings Microsoft Teams via
[Incoming Webhooks](https://learn.microsoft.com/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook) -
no bot registration or Azure AD app needed.

- Copy `teams_webhooks.txt.example` to `teams_webhooks.txt` and put one
  webhook URL per line (blank lines and `#` comments are ignored). See that
  file for how to get a URL from a Teams channel.
- This list is maintained directly by admins editing that file on the
  server - it is **not** exposed through the web UI, and `teams_webhooks.txt`
  is gitignored since each URL can post into that channel on its own (treat
  it like a secret).
- The file is re-read on every new task, so an admin's edit takes effect
  immediately - no app restart needed.
- Every URL in the file gets the same notification (title, points,
  priority, deadline, required skills if any, and the creator's name).
  Delivery is best-effort per URL: a bad or unreachable webhook is logged
  and skipped rather than blocking task creation for everyone else.
- Set `APP_BASE_URL` (env var) once the app is reachable at a real address
  and the notification will include a "View task board" link; leave it
  unset while running locally.

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
  models.py         User, Task, TaskEligibility
  utils.py          parse_skills() - shared skill-matching helper
  auth.py           login/logout routes
  tasks.py          task board, claim/status/reassign/run-selection, leaderboard
  admin.py          worker list, skills editing, add-worker (admin role only)
  notifications.py  MS Teams webhook fan-out on new tasks
  templates/        Jinja templates (+ htmx partial for task rows)
  static/style.css
seed.py                    one-off script to create user accounts
run.py                     dev server entrypoint
config.py                  SECRET_KEY / DB URL / Teams webhook file, overridable via env vars
teams_webhooks.txt.example template - copy to teams_webhooks.txt (gitignored) and fill in
```

Data lives in a single SQLite file (`taskbidder.db`), created automatically.
There's no migration tool yet (just `db.create_all()`), so if you have an
existing local `taskbidder.db` from before the skills/eligibility feature,
delete it and rerun `python seed.py` rather than trying to upgrade it in place.

## Follow-ups (not built yet, deliberately out of scope for v1)

- Self-service password change / admin user management UI beyond the basic
  add-worker and skills-editing forms.
- Notifications only cover new tasks - nothing yet for reassignment,
  approaching deadlines, or a task going stale with no claims.
- Points-based bidding/auction instead of first-come claiming.
- Badges / streaks beyond the raw points leaderboard.
- Richer skill matching (fuzzy/partial match, a controlled skill vocabulary
  instead of free text, "any of" in addition to "all of").
- Auto re-running selection (e.g. on a schedule, or whenever a worker's
  skills change) instead of requiring an explicit admin click.
