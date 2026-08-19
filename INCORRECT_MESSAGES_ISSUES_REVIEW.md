# Incorrect Messages / Issues — Backend Review

Checked against the current code. Two of these scenarios are **new**
backend findings; the rest repeat scenarios already tracked in
`APP_ISSUES_BACKEND_ANALYSIS.md` — those are cross-referenced rather than
re-documented, so the two files don't drift out of sync. No code was
changed to produce this document.

---

## New backend issues found

### 1. Review submission requires a comment/note — backend enforces this, not just the app

**Files:** `openup_api/views/feedback_views.py` (`add_feedback`), `openup_app/serializers.py` (`FeedbackSerializer`), `openup_app/models.py` (`Feedback`)

This is a genuine backend requirement, not just a frontend validation choice:

- `add_feedback()` explicitly rejects the request if the comment is missing:
  ```python
  if feedback_star is None or feedback_comment is None:
      return JsonResponse({
          "success"    :   0,
          "message"   :   "please provide data"
      })
  ```
  (feedback_views.py:67-71)
- Even if an empty string were sent instead of omitting the field entirely,
  `FeedbackSerializer.feedback_comment` is a plain
  `serializers.CharField(max_length=500)` (serializers.py:268) with no
  `required=False`/`allow_blank=True`, and the underlying model field
  `Feedback.feedback_comment` (models.py:359) is a `CharField(max_length=500)`
  with no `null=True`/`blank=True` either — DRF's default `CharField`
  rejects blank values, so the serializer would fail validation and
  `add_feedback` would return the generic `"error occured"` message.

So a star-only review is currently impossible through this API regardless
of what the app does on its end.

**Solution:**
- In `add_feedback()`, change the required-field check to only require
  `feedback_star` (drop `feedback_comment is None` from the condition).
- In `FeedbackSerializer`, make `feedback_comment` optional:
  `serializers.CharField(max_length=500, required=False, allow_blank=True, default='')`.
- In the `Feedback` model, allow blank/null comments:
  `models.CharField(max_length=500, blank=True, default='')` (a migration
  would be needed for the model change).

---

### 2. Customer's star rating/review is never surfaced to the employee

**Files:** `openup_api/views/job_views.py`

Confirmed by searching the whole file: `Feedback`, `feedback_stars`, and
`feedback_comment` are never referenced anywhere in `job_views.py`. Neither
`employee_joblist()`, `job_details()`, `build_job_payload()`, nor
`active_job()` join or return the `Feedback` row for a job. So even once a
review is submitted, there's currently no backend path for it to reach the
employee's "My Job" page alongside the job details.

**Solution:** in `build_job_payload()` (used by `job_details()`/`active_job()`)
and/or `employee_joblist()`, look up the job's `Feedback` row (if any) via
`feedback_job=job_data` and include `feedback_stars`/`feedback_comment` in
the response for completed jobs.

---

## Not a backend issue

### Location permission ("while using the app" not recognized)

No backend code is involved in requesting, checking, or storing location
permission state — that's entirely handled by the OS-level permission APIs
on the device (Android/iOS) and the app's own permission-check logic. There
is nothing in `openup_api`/`openup_app`/`openup` that could cause this
message to appear incorrectly. This is a mobile-app-only fix.

---

## Already tracked in `APP_ISSUES_BACKEND_ANALYSIS.md` — not duplicated here

| Scenario in this message | Covered by |
|---|---|
| Before/after pictures not shown in Job Details / not accessible in "My Job" | Issue #2 (and #3 for the photo-required-before-completion validation) |
| Job complete — too many notifications / review page not auto-popping | Issue #4 (backend already sends exactly one notification, only to the client — the missing piece is the auto-open signal in the payload) |
| No employees available — contradicting screen/notification messages | Issue #5 |
| Job rejected by all employees — same problem as above | Issue #6 (`reject_job()` stub) |
| Google Maps / FCM key hygiene, serializer bug, plaintext passwords | Issues #7-#10 |

## Reconfirmed as already handled on the backend (no new gap found this pass)

- **Customer cancels — job still available to employees.** Re-checked:
  `employee_joblist()` still excludes `job_status_id=4`, `accept_job()` and
  `job_details()` still block acting on a cancelled job, and `cancel_job()`
  still broadcasts a `'cancel_job'` push. If this is still observed in
  testing, the backend state is correct at the time of cancellation — the
  gap is most likely the app not refreshing/reacting to the push, not a
  server-side omission.
- **"Some error occurred" when cancelling from the Directions page.**
  Re-checked: `cancel_job_by_employee()` still returns specific, distinct
  messages for every anticipated failure case, never the generic string
  reported. Points at the app not displaying the response's `message`
  field, or a call site outside the ones this endpoint covers.
- **Employee can't get back into a job after exiting the app.** Re-checked:
  `/api/active-job` and `employee_joblist()`'s alerted-job logic still
  return a not-yet-actioned job regardless of push-notification dismissal.

## Not backend issues (frontend only, per your own proposed solutions)

- "Are you sure?" confirmation prompts for reject/cancel.
