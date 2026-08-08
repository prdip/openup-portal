# Notifications — What Sends, When, To Whom

Everything below reflects the **current code** in
`openup_api/views/job_views.py` (all push sends go through
`FCM.send_notification()` in `openup/fcm.py`). Each section is one job
event: the function that fires it, the exact condition that must be true,
who receives it, and the exact payload.

---

## 1. Job created — `add_job()` → `jobAlert()`

**Trigger:** client calls `POST add_job`. `jobAlert()` is a Celery task
(`@shared_task`), but `add_job()` calls it **directly (synchronously)** rather
than via `.delay()`, because it needs the return value to set the
`no_availability` flag on its own response (see the note at the end of this
section). Every other `jobAlert()` call site dispatches it with `.delay()`.

**Condition / logic:** searches active employees (`employee_status=1`,
`user_role_id=1`, role adjusted for `job_type == "emergency"`), and for each
one calls the Google Distance Matrix API — only employees within **1260
seconds (21 min)** drive time of the job's location qualify.

### 1a. At least one employee qualifies
| | |
|---|---|
| **Recipient** | Every qualifying employee (looped individually) |
| **Title** | `New job request` |
| **Message** | `"EMERGENCY!!! PLEASE ACCEPT THIS JOB ASAP!!!"` (emergency job, first alert or emergency re-alert) / `"PLEASE ACCEPT THIS JOB ASAP!!!"` (normal job, first alert) / `"PLEASE ACCEPT THIS JOB!!!"` (normal job, re-alert after an exclusion list exists) |
| **notificationScreenType** | `addjob` |
| **job_status set to** | `1` (active) |
| **Side effect** | An `Alerts` row is saved recording which employee ids were notified |

### 1b. No employee qualifies
| | |
|---|---|
| **Recipient** | The client |
| **Title** | `Not Accepted` |
| **Message** | `We are currently not available in your area, coming soon` |
| **notificationScreenType** | `no_availability` |
| **job_status set to** | `5` |

> **Sync fallback for the waiting screen.** Because `jobAlert()` runs inside
> `add_job()`, when no employee qualifies the `add_job` response itself also
> carries `notificationScreenType: no_availability` plus the same `message`
> (inside `data`), so the app can switch its "Hang tight..." screen without
> relying on the push being delivered/tapped.

---

## 2. Employee accepts — `accept_job()` → `accept_job_notification()` (Celery task)

**Trigger:** `POST job_accept`, dispatched via `.delay()` (background).

**Condition:** the job isn't already `accepted`(2)/`completed`(3), and isn't
`canceled by client`(4). On success `job_status` is set to `2` and
`job_accepted_by` is set to the accepting employee.

| | |
|---|---|
| **Recipient** | The client |
| **Title** | `job acepted` *(typo in source)* |
| **Message** | `Your job accepted` |
| **notificationScreenType** | `acceptjob` |

---

## 3. Job completed — `complete_job()` → `complete_job_notification()` (Celery task)

**Trigger:** `POST complete_job`, dispatched via `.delay()` (background).

**Condition:** requester must be the currently accepted employee; job must
not already be `completed`(3) or `canceled by client`(4); **and** the job
must have at least one `Images` row with `img_type=1` (before) and at least
one non-`1` (after) — enforced server-side, request is rejected with
`"Please upload both before and after pictures before completing the job"`
otherwise. On success `job_status` is set to `3`.

| | |
|---|---|
| **Recipient** | The client only — never the employee |
| **Title** | `job completed` |
| **Message** | `Your job completed. Please add review about your job` |
| **notificationScreenType** | `completejob` |
| **Extra flag** | `showReviewPage: true` — tells the app to auto-open the review screen |

---

## 4. Client cancels — `cancel_job()` → `cancel_job_notification()` (Celery task)

**Trigger:** `POST cancel-job`, dispatched via `.delay()` (background).

**Condition:** job isn't already `job_status=4`. On success `job_status` is
set to `4`, `job_accepted_by` cleared, and the previous acceptor (if any) is
appended to `job_attempted_by`.

| | |
|---|---|
| **Recipient** | **Every** active employee matching role/status — no distance filtering, not scoped to who was previously alerted about this specific job |
| **Title** | `Cancel Job` |
| **Message** | `The job has been cancelled` |
| **notificationScreenType** | `cancel_job` |

---

## 5. Employee cancels — `cancel_job_by_employee()` → `notify_client()` (Celery task)

**Trigger:** `POST cancel-job-by-emp`. Requester must be the currently
accepted employee; job must not already be `completed`(3),
`canceled by client`(4), or `no-employees-available`(5). On success
`job_status` resets to `1`, `job_accepted_by` is cleared, and the cancelling
employee is appended to `job_attempted_by`.

**`notify_client()`** (async, dispatched with `.delay()`) is the only thing
fired for this event:
1. Unconditionally sends the client: title `Job Cancelled by Employee. This
   job is active now`, message `This job has been cancelled by the
   employee.Your job is active now`, `notificationScreenType: cancel_job`.
2. Then re-runs the same nearby-employee search as `jobAlert()` (1260s
   distance-matrix threshold, excluding the cancelling employee and everyone
   in `job_attempted_by`):
   - Matches found → each matched employee gets `New job request` /
     `addjob` (same as section 1a); `job_status` set back to `1`; a new
     `Alerts` row is saved.
   - No matches → client gets a second notification, `Not Accepted` /
     `no_availability` (same as section 1b, message
     `We are currently not available in your area, coming soon`);
     `job_status` set to `5`.

> **Fixed — duplicate sends.** `cancel_job_by_employee()` used to call
> `jobAlert()` as well, which independently repeated the *identical*
> nearby-employee search, so every qualifying employee got the `New job
> request` push **twice** and two `Alerts` rows were written per cancellation.
> The redundant `jobAlert()` call has been removed — `notify_client()` already
> covers both the client notice and the employee re-alert, so it is now one
> push per employee and one `Alerts` row.

---

## 6. Employee rejects — `reject_job()` → `jobAlert()` (Celery task)

**Trigger:** `POST reject_job`. Job must not be `canceled by client`(4),
`completed`(3), or already `no-employees-available`(5). On success the
rejecting employee is appended to `job_attempted_by` and a `JobLogs` entry
(`"Job rejected by employee"`) is written.

**Notification:** `reject_job()` sends nothing itself — it re-runs
`jobAlert()` via `.delay()` (background, same 1260s search as section 1),
which then sends whichever of 1a/1b applies:
- Other qualifying employees get `New job request` / `addjob`.
- If nobody's left, the client gets `Not Accepted` / `no_availability` and
  `job_status` becomes `5` — this is also how "all employees reject" ends
  up in the same state as "nobody was available in the first place."

---

## Celery

Every notification function is a registered Celery task
(`@shared_task()`), so pushes and the Distance Matrix lookups they depend on
run on the worker instead of blocking the HTTP request:

```
openup_api.views.job_views.jobAlert
openup_api.views.job_views.accept_job_notification
openup_api.views.job_views.complete_job_notification
openup_api.views.job_views.cancel_job_notification
openup_api.views.job_views.notify_client
```

The one deliberate exception is `add_job()`, which calls `jobAlert()`
directly rather than with `.delay()` — a `@shared_task` function is still an
ordinary callable when invoked without `.delay()`, and `add_job` needs the
return value to put the `no_availability` signal in its own response. Every
other call site uses `.delay()`.

**The worker must be running** for these to be delivered — without it,
`.delay()` calls queue in Redis and are never processed, with nothing in the
request/response cycle indicating failure:

```
celery -A openup.celery worker -l INFO
```

---

## Quick reference table

| Event | Function | Async? | Recipient | notificationScreenType |
|---|---|---|---|---|
| Job created, employees found | `jobAlert` | No — sync in `add_job` by design | Matched employees | `addjob` |
| Job created, no employees | `jobAlert` | No — sync in `add_job` by design | Client | `no_availability` |
| Employee accepts | `accept_job_notification` | Yes | Client | `acceptjob` |
| Job completed | `complete_job_notification` | Yes | Client only | `completejob` (+ `showReviewPage`) |
| Client cancels | `cancel_job_notification` | Yes | All active employees | `cancel_job` |
| Employee cancels — client notice | `notify_client` | Yes | Client | `cancel_job` |
| Employee cancels — re-alert (found) | `notify_client` | Yes | Matched employees | `addjob` |
| Employee cancels — re-alert (none) | `notify_client` | Yes | Client | `no_availability` |
| Employee rejects | `jobAlert` (via `reject_job`) | Yes | Matched employees or client | `addjob` or `no_availability` |
