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

16. > commit and push the latest code including the teams notification code
    >
    > → committed the Teams notification feature (`382beb8`) and this history
    > log (`5925b87`) as separate commits and pushed both to `origin/main`.

## 2026-09-18

17. > create a flow diagram indicating lifecycle of a task on this utility and
    > roles played by different actors and different 3rd party tools like MS
    > Teams.
    >
    > → published an artifact (`docs/lifecycle-diagram.html`) with two
    > diagrams: the full task state machine with each transition attributed
    > to the actor who triggers it, and a detail view of the skill-eligibility
    > "snapshot, not live" matching mechanism.

18. **Scope addition - creator approval gate**:
    > when a task is marked done, the respective task creator needs to vet it
    > and approve as done. this will have to be coded in too.
    >
    > → added a `pending_review` stage between `in_progress` and `done`. A
    > worker can only push a task as far as `pending_review`; only that
    > task's own creator (not any creator - narrower than reassignment) can
    > approve it into `done` or reject it back to `in_progress`. Points still
    > only credit on `done`, so nothing pays out until the owner approves.
    > Updated the lifecycle diagram artifact to match.

19. **Scope addition - notify C group on claim and on submission**:
    > when a task gets picked up by a worker and when a worker marks a task
    > as done, a MS Teams message needs to be triggered to all members of
    > the C group. The Teams IDs of all C group members can be assumed in
    > another simple text file.
    >
    > (first attempt was interrupted before any action was taken; clarified
    > on retry:) the message must carry the name of the worker picking up
    > the task, and that the said worker marked the task as done. ("done"
    > confirmed to mean the worker's submit-for-review action, not the
    > owner's final approval.)
    >
    > → added `notify_task_claimed()` and `notify_task_submitted_for_review()`,
    > both fanning out to a new admin-maintained `teams_webhooks_creators.txt`
    > (separate list from `teams_webhooks.txt`) so every C-group member hears
    > about it regardless of who owns the task. Each message names the
    > worker. Approval/rejection deliberately stays silent - not requested.

20. **Correction - eligibility refresh should be global, not per-task**:
    > the Admin's eligibility compute task should not be manual. Creator of
    > the task already defines criteria for Worker filtering for his task.
    > The Admin only triggers a process where the Worker filtering needs to
    > be refreshed because the sample space of W keeps changing.
    >
    > → removed the per-task "Run selection" button and its route entirely.
    > Replaced with a single global "Refresh worker eligibility for all
    > tasks" action on the Workers page that recomputes every non-`done`
    > task with a skill requirement in one pass. Extracted the matching
    > logic into `refresh_task_eligibility()` in `utils.py` so it's shared
    > rather than duplicated. Also caught and fixed an unrelated bug found
    > while testing: the task-list status filter dropdown was missing
    > `pending_review` from the approval-gate feature. Updated the lifecycle
    > diagram artifact's wording to match ("refresh" replacing "run
    > selection" throughout, and the detail diagram's caption now explains
    > it as one global pass viewed through a single task).

21. **Redesign - mandatory skills, per-worker filtering, and admin override powers**:
    > I still see a problem with the filtering. My bad in defining it
    > improperly.
    >
    > Soon as a C creates a task with required_skills (make this mandatory)
    > the filtering is derived from it, and the MS Teams message is sent to
    > the filtered sub-set of Ws only. This way tasks are shown to only
    > eligible Ws.
    >
    > Admin may just manually intervene in editing the filter criteria or
    > overriding a W's bid and reassign to open.
    >
    > (clarified via two questions: per-worker Teams targeting needs a
    > username-to-webhook mapping file rather than a shared channel; a
    > worker's own claimed/in-progress task must stay visible to them even
    > if the pool later shifts against them.)
    >
    > → `required_skills` is now mandatory (`nullable=False`, required in
    > the form) and eligibility is computed automatically the instant a
    > task is created - no more waiting on an admin action for the initial
    > pass. The `/tasks` board is now filtered server-side per worker: an
    > ineligible task doesn't appear at all (not even disabled), except a
    > worker always keeps seeing tasks already assigned to them. The
    > new-task Teams notification switched from a broadcast list
    > (`teams_webhooks.txt`, removed) to a per-worker map
    > (`teams_webhooks_workers.txt`, "username,webhook_url" per line) and
    > now reaches only the workers in that task's eligibility snapshot.
    > Added an admin-only inline "edit required_skills" control on each
    > task row that force-recomputes just that task's eligibility. Widened
    > the reassign-override to `is_creator or is_admin` (previously
    > creator-only) so a pure admin account - even one that's a worker, not
    > a creator - can override a claim and reopen a task. The admin's
    > global "Refresh worker eligibility" action from the previous entry is
    > unchanged and still handles ongoing pool drift after creation.
