# Rejected-Job-After-Accept Visibility Issue

## Scenario

Two employees are in range of a client's job:

1. Employee A **accepts** the job (job becomes `job_status=2`/accepted, `job_accepted_by=A`).
2. Employee A then **rejects** the same job.
3. Expected: the job becomes active again. Employee B (the other employee in range)
   should see the job as normal (with the accept button). Employee A should still see
   the job, but without the process/accept button.

## Actual behaviour (BUG)

- Employee B does **not** see the job at all.
- Employee A still sees the job as "accepted" / assigned (frontend can show the process
  button even though A rejected it).

## Root cause

`reject_job` in `openup_api/views/job_views.py` (lines 1293-1388):

- Records the rejection only by appending the employee to `job_attempted_by` and writing
  a `JobLogs` row.
- It does **NOT** reset `job_status` back to `1` (active) and does **NOT** clear
  `job_accepted_by`.

So after "accept then reject", the job stays in `job_status=2` with `job_accepted_by=A`.

Consequences:

1. **Employee B** - `employee_joblist` (`job_views.py` line 2142-2150) only includes
   active jobs (`job_status_id=1`) that the employee has not attempted, or jobs already
   assigned to that employee. Because the job is still `job_status=2` and
   `job_accepted_by=A`, it is invisible to B.

2. **Employee A** - the job still matches `Q(job_accepted_by=user_id)`, so it appears in
   A's list with `is_assigned=1` and `job_status="accepted"`, so the app can still show
   the process button.

## Reference (correct implementation)

`cancel_job_by_employee` (`job_views.py` lines 1772-1788) does this correctly: it resets
`job_status=1`, sets `job_accepted_by=None`, and appends the employee to
`job_attempted_by`.

## Proposed fix (NOT applied yet - awaiting command)

In `reject_job`, when the job was accepted (`job_status_id == 2`) by the rejecting
employee, mirror `cancel_job_by_employee`:

- Set `job_status = 1`
- Set `job_accepted_by = None`
- Keep appending the employee to `job_attempted_by`

This makes the job active again so employee B sees it with `can_accept=1`, while
employee A still sees it but with `can_accept=0` / `is_assigned=0` (no process button),
because A is already in `job_attempted_by`.

## Status

FIX APPLIED in `openup_api/views/job_views.py` (`reject_job`): when the rejecting
employee had accepted the job, `job_status` is reset to `1` (active) and
`job_accepted_by` is cleared, so the job reappears for other nearby employees while the
rejecting employee keeps seeing it without the process button (stays in
`job_attempted_by`).
