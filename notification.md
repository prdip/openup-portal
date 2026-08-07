# Notifications — What Sends, When, To Whom

Everything below reflects the **current code** in
`openup_api/views/job_views.py` (all push sends go through
`FCM.send_notification()` in `openup/fcm.py`). Each section is one job
event: the function that fires it, the exact condition that must be true,
who receives it, and the exact payload.

---

## 1. Job created — `add_job()` → `jobAlert()`

**Trigger:** client calls `POST add_job`. `jobAlert()` runs **synchronously**
inside that same request (not a background task).

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

## 5. Employee cancels — `cancel_job_by_employee()` → `notify_client()` (Celery task) **and** `jobAlert()` (direct call)

**Trigger:** `POST cancel-job-by-emp`. Requester must be the currently
accepted employee; job must not already be `completed`(3),
`canceled by client`(4), or `no-employees-available`(5). On success
`job_status` resets to `1`, `job_accepted_by` is cleared, and the cancelling
employee is appended to `job_attempted_by`.

Both of the following fire for the **same** cancellation event:

**`notify_client()`** (async):
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

**`jobAlert()`** (called directly, synchronously, right after
`notify_client.delay(...)`): independently repeats the **identical**
nearby-employee search and send logic described in section 1.

> **Known bug — duplicate sends.** Because both are triggered for the same
> event, every employee who qualifies gets the `New job request` push
> **twice**, and two `Alerts` rows are written for one cancellation. This is
> the current behavior, not a documentation error.

---

## 6. Employee rejects — `reject_job()` → `jobAlert()` (direct call)

**Trigger:** `POST reject_job`. Job must not be `canceled by client`(4),
`completed`(3), or already `no-employees-available`(5). On success the
rejecting employee is appended to `job_attempted_by` and a `JobLogs` entry
(`"Job rejected by employee"`) is written.

**Notification:** `reject_job()` sends nothing itself — it re-runs
`jobAlert()` (synchronously, same 1260s search as section 1), which then
sends whichever of 1a/1b applies:
- Other qualifying employees get `New job request` / `addjob`.
- If nobody's left, the client gets `Not Accepted` / `no_availability` and
  `job_status` becomes `5` — this is also how "all employees reject" ends
  up in the same state as "nobody was available in the first place."

---

## Not part of the live notification flow

`job_alert_after_cancel()` in `job_views.py` contains a third copy of the
same nearby-employee search/notification logic, but has **no call sites**
anywhere in the codebase — it never fires. Not documented above as a live
path since it's dead code.

---

## Quick reference table

| Event | Function | Async? | Recipient | notificationScreenType |
|---|---|---|---|---|
| Job created, employees found | `jobAlert` | No (sync in `add_job`) | Matched employees | `addjob` |
| Job created, no employees | `jobAlert` | No (sync in `add_job`) | Client | `no_availability` |
| Employee accepts | `accept_job_notification` | Yes | Client | `acceptjob` |
| Job completed | `complete_job_notification` | Yes | Client only | `completejob` (+ `showReviewPage`) |
| Client cancels | `cancel_job_notification` | Yes | All active employees | `cancel_job` |
| Employee cancels — client notice | `notify_client` | Yes | Client | `cancel_job` |
| Employee cancels — re-alert (found) | `notify_client` + `jobAlert` (duplicate) | Mixed | Matched employees | `addjob` (sent twice) |
| Employee cancels — re-alert (none) | `notify_client` + `jobAlert` (duplicate) | Mixed | Client | `no_availability` (sent twice) |
| Employee rejects | `jobAlert` (via `reject_job`) | No (sync) | Matched employees or client | `addjob` or `no_availability` |
