# Prompt History

A chronological log of the prompts driving this project's development in
Claude Code. Kept for reference - not part of the application itself.

## 2026-09-10

1. **Initial ask** - high-level design request:
   > Let's build a task-bidder utility. I have a team C of 4 or 5
   > task-creators. And then I have a team W of 10 or 20 task-workers/engineers.
   > I want to create a gamified bidding-based system for W group members to
   > bid or pick from tasks created by C group and update status after
   > working on the tasks. And I want a web interface for C group to enter
   > contents and create a task. The W group might also need a similar web
   > interface or a MS Teams based ping utility to flag a new task waiting
   > for bidding. Come up with a high-level structure for this utility.
   >
   > → produced a high-level architecture proposal (entities, bidding
   > mechanics options, system diagram, notification strategy, stack
   > suggestion, phased plan).

2. **Scope down to a real build**:
   > Let's start a new, real project with this goal. But let's keep it
   > simple now. The bidding mechanic will be the simple claim method only.
   > Dont need a different view for C & W groups. In fact both groups see
   > the same view with their logins, both see list of tasks, a leaderboard
   > showing points earned by members of W group. Once a task is bid and
   > picked by one W member, it can only be re-assigned by a C member. Both
   > group members will have option to filter tasks based on owner/assignee.
   >
   > → clarified stack (Flask + SQLite + HTMX) and auth (session-based
   > username/password) via follow-up questions, then scaffolded and tested
   > the app end-to-end.

3. **Version control**:
   > git init and commit this initial scaffold
   >
   > → `git init`, staged the app, created the first commit.

4. > what's the github repo name?
   >
   > → clarified no GitHub repo existed yet; offered to create one.

5. **Create and push to GitHub**:
   > yes, let's also push this to a new git repo - task-bidder is a good
   > name for this git repo. You should create this repo in my git profile
   > https://github.com/rohith-mirafra
   >
   > → no `gh` CLI or existing GitHub auth found on the machine; asked how
   > to authenticate.

## 2026-09-15

6. **(Answering the auth question)**:
   > see if this file can help access my github authentication:
   > /home/rohithbatni/RMS_Summarize/.git/ORIG_HEAD
   >
   > → that file turned out to be unrelated to auth (just git's last-HEAD
   > bookkeeping); found an existing SSH deploy key for a different repo,
   > explained it wouldn't work here (deploy keys are repo-scoped), and
   > asked again how to authenticate.

7. > empty repo created - https://github.com/rohith-mirafra/task-bidder
   >
   > → generated a new SSH keypair on the machine and asked the user to add
   > the public key to their GitHub account.

8. > done, push it
   >
   > → attempted the push; the first SSH auth test failed (turned out to be
   > a test-command bug on my end, not a real auth problem).

9. > try it again
   >
   > → found and fixed the test bug, confirmed SSH auth worked, pushed the
   > initial commit to `origin/main`, and set the repo to use the right key
   > by default for future pushes.

## 2026-09-17

10. > do a status check of the objectives of this project
    >
    > → reviewed git state and re-checked every original objective against
    > what was actually built; flagged the MS Teams notification and real
    > team-member accounts as the two open items.

11. **Scope addition - skill-based worker selection**:
    > some scope addition...
    >
    > the group of workers for any given task could be different. depending
    > on the task the W group needs to be built from a larger, constantly
    > growing W group. this 'selection' of workers from the larger W group
    > will need to be redone periodically, when triggered by the Admin. the
    > criteria for selection of workers is specified once per task, coded as
    > a set of skills or capabilities of workers, perhaps in a plain text
    > format.
    >
    > go ahead and build the skeleton structure to accommodate this.
    >
    > → added `required_skills` (per task, set by its creator) and worker
    > `skills`, plus an admin-only "Run selection" action that snapshots
    > which current workers qualify; the Claim button is gated by that
    > snapshot. Also added an admin-only Workers page (add workers, edit
    > skills) and introduced an `admin` role.

12. **Correction - admin is a flag, not a role**:
    > admin is a status indicator. it could be more than one person. and any
    > of these admins could be task creators too.
    >
    > all task creators should be able to define criteria for W selection
    > for only the task they create.
    >
    > → changed `admin` from a third mutually-exclusive role into an
    > independent `is_admin` boolean any user (creator or worker) can carry,
    > so a creator can also be an admin on one account and more than one
    > person can hold it; confirmed criteria-setting was already
    > creator-owned and unaffected by admin status.

13. > commit this as one change and push
    >
    > → committed the skill-selection feature and the admin-flag fix
    > together (`db05826`) and pushed to `origin/main`.

14. **MS Teams notifications**:
    > build the MS Teams notification for new tasks, where the list of
    > Teams IDs is maintained by Admin(s) in a text file.
    >
    > → added `app/notifications.py`, which reads Incoming Webhook URLs from
    > an admin-maintained `teams_webhooks.txt` (gitignored; template checked
    > in as `teams_webhooks.txt.example`) and posts a MessageCard to each on
    > every new task, with per-URL failure isolation so a bad webhook can't
    > block task creation. Verified against a local mock server.

15. > create a history log of my prompts on this project in the working dir.
    >
    > → this file.
