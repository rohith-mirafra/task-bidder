# Task Bidder

A small internal tool for a creator team (C) to post tasks and a worker team (W)
to claim, work, and complete them for points. Everyone shares the same task
board and leaderboard view; permissions differ by role, not by page.

## How it works

- **Creators** create tasks (title, description, points, priority, deadline,
  and a **mandatory** required-skills string - see below).
- **Workers** only ever see tasks they're currently eligible for on their
  board, and claim any `open` one on a first-come basis. Claiming assigns
  it to them and moves it to `claimed`.
- The assignee moves their own task forward: `claimed` -> `in_progress` ->
  `pending_review`. A worker can get a task to `pending_review` but cannot
  mark it `done` themselves.
- Only the task's **own creator** (not any creator - the specific owner)
  can approve a `pending_review` task into `done`, or reject it back to
  `in_progress` for more work. This is deliberately narrower than
  reassignment below.
- Any **creator or admin** can reassign a task to a different worker or
  send it back to `open`, at any stage before `done` (including
  `pending_review`) - overriding both the current assignee and the skill
  filter outright. This is the explicit escape hatch for "override a
  worker's bid."
- Everyone can filter the task list by owner (creator) and by assignee (worker).
- The leaderboard sums points from `done` tasks per worker - a task sitting
  in `pending_review` doesn't pay out until its creator approves it.

## Worker selection by skill (per task)

The worker pool (W) is larger than any one task needs and keeps growing, so
every task is filtered down to just the workers who can actually do it:

- Each task's creator sets `required_skills` once, at task creation - free
  text, comma-separated (e.g. `python, aws`), and it's **mandatory**: every
  task is skill-gated, there's no "open to everyone" option. Only that
  task's creator sets it at creation time - it isn't an admin power.
- Each worker has a `skills` field (also free text, comma-separated),
  managed on the **Workers** page (visible to admins only).
- Matching is "worker has all of the task's required skills," and it's
  computed **immediately when the task is created** - the board and the
  Teams notification (below) both reflect real eligibility from the start,
  not an empty snapshot waiting on a manual step.
- The catch: it's a snapshot, not a live check, so it goes stale as the
  worker pool changes after that (new workers join, existing ones update
  their skills). There's no per-task button to fix that: an **admin**
  clicks one global **Refresh worker eligibility** action on the Workers
  page, and it recomputes every non-`done` task in a single pass.
- **Workers only see tasks they're currently eligible for** on their board
  - an ineligible task doesn't show up at all, not even with a disabled
  Claim button. The one exception: once a worker is assigned to a task,
  they keep seeing and can keep working it even if eligibility later
  drifts against them (e.g. an admin changes the criteria, or the snapshot
  goes stale) - only the ability to *newly claim* something is gated,
  never a worker's own in-flight work. Creators and admins always see
  every task, filtered by nothing but the owner/assignee/status dropdowns.
- An **admin** can also edit a task's `required_skills` directly (inline on
  the task row), which always force-recomputes that one task's eligibility
  immediately - independent of, and in addition to, the global refresh.
- The task row shows the requirement, the eligible worker count, and the
  last-refresh timestamp.

`admin` is a status (`User.is_admin`), not a third role - it's independent
of `role` (`creator`/`worker`), more than one person can hold it, and it
can sit on a creator *or* a worker account (seed data gives two of the four
seeded creators the flag as an example). It unlocks the Workers page,
refreshing/editing eligibility, and - jointly with creators - the
reassign-override; it grants no extra power over creating tasks, which is
still strictly a creator's job.

This is a skeleton: matching is a simple set-membership check (no fuzzy
matching, synonyms, or weighting).

## MS Teams notifications

The app pings Microsoft Teams via
[Incoming Webhooks](https://learn.microsoft.com/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook) -
no bot registration or Azure AD app needed - on three events. New-task
notifications are **filtered per person**; the other two **broadcast**:

| Event | Who it's sent to | List file | Format |
|---|---|---|---|
| A creator posts a new task | only workers currently eligible for it | `teams_webhooks_workers.txt` | `username,webhook_url` per line |
| A worker claims a task | every C-group member | `teams_webhooks_creators.txt` | one webhook URL per line |
| A worker marks a task done (submits for review) | every C-group member | `teams_webhooks_creators.txt` | one webhook URL per line |

- Copy each `*.example` file to drop the `.example` suffix and fill it in
  (blank lines and `#` comments are ignored in both). See either file for
  how to get a webhook URL from Teams.
- `teams_webhooks_workers.txt` needs one line per worker who should hear
  about new tasks - a personal Incoming Webhook (a 1:1 chat or personal
  channel), keyed by their login username. A worker with no entry, or who
  isn't currently eligible for a given task, hears nothing about it -
  eligibility is computed right before this notification goes out, so it's
  always accurate as of that moment.
- Both lists are maintained directly by admins editing the files on the
  server - **not** exposed through the web UI - and both are gitignored
  since each URL can post (or, for the worker file, DM) on its own (treat
  them like secrets).
- Both files are re-read on every event, so an admin's edit takes effect
  immediately - no app restart needed.
- The claimed/submitted-for-review notifications name the worker (e.g.
  "Alex picked up this task" / "Alex marked this task as done") and go to
  every C-group entry regardless of who owns the task - not just the
  task's own creator, since anyone in C might want to know.
- Delivery is best-effort per URL, for all three events: a bad or
  unreachable webhook is logged and skipped rather than blocking the
  action that triggered it.
- Set `APP_BASE_URL` (env var) once the app is reachable at a real address
  and notifications will include a "View task board" link; leave it unset
  while running locally.

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
  tasks.py          task board, claim/status/review/reassign/edit-skills, leaderboard
  admin.py          worker list, skills editing, add-worker, refresh-eligibility (admin only)
  notifications.py  MS Teams webhook fan-out (new task / claimed / submitted for review)
  templates/        Jinja templates (+ htmx partial for task rows)
  static/style.css
seed.py                             one-off script to create user accounts
run.py                              dev server entrypoint
config.py                           SECRET_KEY / DB URL / Teams webhook files, overridable via env vars
teams_webhooks_workers.txt.example  template - copy to teams_webhooks_workers.txt (gitignored)
teams_webhooks_creators.txt.example template - copy to teams_webhooks_creators.txt (gitignored)
```

Data lives in a single SQLite file (`taskbidder.db`), created automatically.
There's no migration tool yet (just `db.create_all()`), so if you have an
existing local `taskbidder.db` from before the skills/eligibility feature,
delete it and rerun `python seed.py` rather than trying to upgrade it in place.

## Follow-ups (not built yet, deliberately out of scope for v1)

- Self-service password change / admin user management UI beyond the basic
  add-worker and skills-editing forms.
- No notification yet for reassignment, approaching deadlines, or a task
  going stale with no eligible workers at all.
- Points-based bidding/auction instead of first-come claiming.
- Badges / streaks beyond the raw points leaderboard.
- Richer skill matching (fuzzy/partial match, a controlled skill vocabulary
  instead of free text, "any of" in addition to "all of").
- Auto-refreshing eligibility on a schedule, or whenever a worker's skills
  change - it's automatic at task creation, but drift afterward (new
  workers, edited skills) still needs an admin's manual global refresh.
