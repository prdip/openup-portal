# Backend Issues & Required Changes

Re-checked against the current code for each reported scenario. Only
backend-relevant items are listed with a solution; scenarios that are
frontend-only, or already correctly handled on the backend, are noted
briefly at the end so they aren't mistaken for open work.

---

### 1. Employee (2) doesn't see Accept/Decline on the Job Details page

**Files:** `openup_api/views/job_views.py`

After Employee 1 accepts then cancels a job, Employee 2 opens it and lands
on the **Job Details** page with no Accept/Decline buttons.

`build_job_payload()` (used by `job_details()`) still doesn't compute a
`can_accept`/`is_assigned` flag — confirmed by checking the current file:
that flag only exists in `employee_joblist()` (line 2069) and `active_job()`
(line 2244):

```python
job['can_accept']   =   1 if (job_record.job_status_id == 1 and not has_attempted(job_record,user_id)) else 0
```

`job_details()` never returns this, so the app has no signal to show the
buttons on this screen, even though the job's actual state (status reset to
1, `job_accepted_by` cleared) is correct.

**Solution:** add the same `can_accept`/`is_assigned` computation into
`build_job_payload()`, passing the requesting employee's `user_id` in so the
flag is per-employee.

---

### 2. Before/after pictures not accessible in "My Job/History"

**Files:** `openup_api/views/job_views.py`

Confirmed `client_joblist()` and `employee_joblist()` still return no image
data at all. Only `build_job_payload()` (used by the single-job
`job_details()`/`active_job()`) assembles before/after image lists.

**Solution:** extend `client_joblist()`/`employee_joblist()` to include each
job's before/after image URLs, or add a dedicated history endpoint reusing
`build_job_payload()`'s existing image-assembly logic.

**Related, same scenario's note:** there is still no server-side check in
`complete_job()` requiring at least one "before" and one "after" `Images`
row before allowing `job_status` to move to `3`. Add that validation so the
backend enforces the same rule the "complete" button is supposed to gate.

---

### 3. Job complete — too many notifications / review page not auto-popping

**Files:** `openup_api/views/job_views.py` (`complete_job_notification`)

Confirmed `complete_job_notification()` still sends exactly **one**
notification and only to the client — that part is correct, so it isn't the
source of "too many notifications." But its FCM payload still only carries
`notificationScreenType: "completejob"`, with no flag telling the app to
auto-open the review screen.

**Solution:** add an explicit flag to the payload (e.g.
`"showReviewPage": true`, or a distinct `notificationScreenType`) so the
review page can pop up immediately instead of waiting for a notification
tap. (The "review page shouldn't appear in the employee app" and "exit
without reviewing" parts of this scenario are already satisfied/are
frontend-only — see notes below.)

---

### 4. No employees available / rejected by all — contradicting messages

**Files:** `openup_api/views/job_views.py` (`jobAlert`, `notify_client`)

Confirmed: the "we found employees" and "nobody available" notification
branches still both use `notificationScreenType: 'addjob'`. The app has no
reliable way to distinguish "still searching" from "nobody's available"
from the notification type alone, which is why the on-screen message never
updates to match the notification text.

**Solution:** give the "no employee available" branch (wherever `job_status`
is set to `5`) a distinct `notificationScreenType` (e.g. `'no_availability'`)
so the app can switch its on-screen text to match.

This also covers "rejected by all employees" — same problem, same fix —
plus the missing piece below.

---

* [ ]  5. `reject_job()` is still a non-functional stub

**Files:** `openup_api/views/job_views.py`

Confirmed current code:

```python
def reject_job(request):
    ...
    else:
        # job_id      =       request.data.get(job_id,None)
        return JsonResponse({
            "success"   :    1,
            "message"   :   "job rejected"
            })
```

It verifies the token and always returns success — it never records
anything. So an employee's reject tap doesn't exclude them from future
alerts on that job, and "all employees reject" never actually gets
evaluated, since only cancellations currently feed into the
"not available" path.

**Solution:** implement it — append the rejecting employee to
`job_attempted_by` (same mechanism `cancel_job_by_employee` already uses),
log it, and re-run the area search (`jobAlert`) so that once everyone
eligible has rejected, the job naturally reaches the same "not available"
state as item 4.

---

## Not open backend issues (checked against current code)

- **Customer cancels — job still available to employees.** Still correctly
  handled: `employee_joblist()` excludes `job_status_id=4`, `accept_job()`
  and `job_details()` block acting on a cancelled job, `cancel_job()`
  broadcasts a `'cancel_job'` push. No backend gap found.
- **"Some error occurred" cancelling from the Directions page.** Still
  correctly handled: `cancel_job_by_employee()` returns a specific message
  for every anticipated failure case (missing/invalid job id, not found,
  already cancelled, already completed, no employees available, not the
  current acceptor) — never a generic string. If this still appears, it's
  the app not displaying the response's `message` field.
- **Employee can't get back into a job after exiting the app.** Still
  correctly handled: `/api/active-job` and `employee_joblist()`'s
  alerted-job logic (`available_ids`) return a not-yet-actioned job
  regardless of push-notification dismissal, covering both a pending alert
  and an in-progress accepted job (GPS/job-details resume).

## Not backend issues (frontend/app only)

- "Are you sure?" confirmation prompts before reject/cancel.
- Review page auto-exit back to home without submitting.
- "My Job" menu renamed to "History".
- Review page not appearing in the employee app — backend already only
  notifies the client, nothing to fix here.
