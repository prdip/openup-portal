# OpenUp App Issues - Backend Analysis

**Date:** July 2026  
**Scope:** Identification of backend-required changes from the reported app issues

---

## Executive Summary

Out of the 14 reported issues (3 needing changes, 9 needing fixes, 2 already fixed), **at least 9 require backend changes**. The remaining issues are purely frontend (mobile app) or a mix. Below is a detailed breakdown.

---

## Issues That Require Backend Changes

### ISSUE 1: Employee (2) Cannot Accept/Decline After Employee (1) Cancels

**Status:** NEEDS BACKEND FIX  
**Files:** `openup_api/views/job_views.py`

**Root Cause:** When Employee 1 cancels a job, `cancel_job_by_employee()` resets `job_status=1` (active) and `job_accepted_by=None`, then re-riggers `jobAlert()`. However, the job listing endpoint (`employee_joblist`) likely filters or displays jobs in a way that Employee 2 doesn't see the accept/decline buttons. This is partly a backend issue because:

- The `accept_job()` function checks `job_status` and `job_accepted_by` - this logic is correct.
- The `employee_joblist()` function needs to return the job with proper status indicators so the frontend knows to show accept/decline buttons.
- The `jobAlert()` re-notification may not reach Employee 2 if they were already notified or if exclusion logic (`accepted_by`) incorrectly filters them.

**Backend Fix Required:**
- Ensure `employee_joblist()` returns jobs with `status=1` (active) as available for acceptance regardless of prior cancellation history.
- Verify `jobAlert()` after employee cancellation correctly notifies new employees (excluding only the cancelling employee, not all previously notified ones).
ok
---

### ISSUE 2: Before/After Pictures Not Showing in Job Details / History Page

**Status:** NEEDS BACKEND FIX  
**Files:** `openup_api/views/job_views.py`, `openup_app/models.py`

**Root Cause:** The `getuploaded_image()` endpoint (line ~1900) and `job_details()` (line ~716) both retrieve images. However, there is no dedicated API endpoint to retrieve job history with images for the employee or client "History" page.

**Backend Fix Required:**
- Create a new API endpoint (e.g., `/api/job-history`) that returns completed/canceled jobs with their before/after images for both employees and clients.
- Ensure the `Images` and `File` records are properly returned with full URLs (using `BASE_URL`).
- The `job_details()` already includes images organized by type - verify this data reaches the frontend correctly.

ok
---

### ISSUE 3: Too Many Notifications + Review Page Not Popping Up Automatically

**Status:** NEEDS BACKEND FIX  
**Files:** `openup_api/views/job_views.py`, `openup/fcm.py`

**Root Cause:** The `complete_job_notification` Celery task sends a push notification, but there is no mechanism to:
1. Trigger the review page automatically on the client side.
2. Consolidate notifications - currently multiple notifications may be sent during the job lifecycle.
3. The review page (`add_feedback`) is a passive API endpoint - it doesn't proactively present itself.

**Backend Fix Required:**
- Modify `complete_job_notification` task to send a specific `notificationScreenType` (e.g., `"review"`) in the FCM payload so the mobile app knows to auto-open the review page.
- Ensure only ONE notification is sent at job completion (currently `complete_job_notification` sends one, but verify no duplicate notifications from other tasks).
- The FCM payload should include a flag like `"showReviewPage": true` to instruct the app to auto-open the review modal/screen.

---

### ISSUE 4: Customer-Canceled Job Still Available for Employees

**Status:** NEEDS BACKEND FIX  
**Files:** `openup_api/views/job_views.py`

**Root Cause:** The `cancel_job()` function (line ~1200) sets `job_status=4` (canceled) and triggers `cancel_job_notification` to notify employees. However, the job may still appear in `employee_joblist()` if the listing query doesn't properly filter out canceled jobs.

**Backend Fix Required:**
- Verify `employee_joblist()` filters out jobs with `job_status=4` (canceled).
- Verify `jobAlert()` does not send notifications for canceled jobs.
- Add a real-time mechanism (or polling) so that when a job is canceled, it is immediately removed from all employee job lists. Consider adding a WebSocket or FCM-based "job_removed" event.

ok
---

### ISSUE 5 & 6: No Employees Available / All Employees Reject - Contradictory Messages

**Status:** NEEDS BACKEND FIX  
**Files:** `openup_api/views/job_views.py` (`jobAlert()` function)

**Root Cause:** In `jobAlert()`, when no employees are within the 21-minute radius:
1. The job status is set to 5 (not completed).
2. A notification is sent to the client: "We are currently not available in your area. Coming soon."
3. BUT the frontend screen still shows "Hang tight, we are checking... someone will be with you shortly."

This is a **backend issue** because:
- The backend needs to send a distinct signal/notification that tells the frontend to change the screen message.
- The `cancel_job_notification` for employee rejections also needs to trigger the same "not available" state when all employees reject.

**Backend Fix Required:**
- Add a new `notificationScreenType` value (e.g., `"no_availability"`) in the FCM payload when no employees are available.
- For Issue 6 (all employees reject): The `reject_job()` function is currently a **STUB** (returns success but does nothing). This must be implemented:
  - Track rejection count per job.
  - When all eligible employees have rejected, set `job_status=5` and notify the client with the same `no_availability` screen type.
ok
---

### ISSUE 7: Employee Confirmation Prompt on Reject/Cancel

**Status:** MIXED (Frontend primarily, but backend may need a new endpoint)  
**Files:** `openup_api/views/job_views.py`

**Root Cause:** This is primarily a **frontend** UX issue (adding confirmation dialogs). However:
- The `reject_job()` endpoint is a stub and needs full implementation.
- The backend should log rejection/cancellation with timestamps in `JobLogs`.

**Backend Fix Required:**
- Implement `reject_job()` properly (it's currently a no-op stub).
- Create `JobLogs` entries for rejections.
- Add a "resume job session" mechanism: when an employee exits mid-job and reopens the app, the backend should return the current job state so the app can restore the correct screen.

---

### ISSUE 8: "Some Error Occurred" When Employee Cancels from Directions Page

**Status:** NEEDS BACKEND FIX  
**Files:** `openup_api/views/job_views.py` (`cancel_job_by_employee()`)

**Root Cause:** The `cancel_job_by_employee()` endpoint may be failing because:
- Token validation issues.
- Job state validation (job might already be in a state that doesn't allow cancellation).
- Missing or incorrect request parameters.
- The error is not being properly handled/returned.

**Backend Fix Required:**
- Improve error handling in `cancel_job_by_employee()` to return meaningful error messages instead of generic failures.
- Add proper `try/except` blocks and return specific error codes.
- Ensure the endpoint handles edge cases (job already completed, job already canceled, etc.).
okay
---

### ISSUE 9: Employee Cannot Re-Access Job After Exiting App

**Status:** FIXED (backend)  
**Files:** `openup_api/views/job_views.py`

**Root Cause:** When an employee taps a job via notification and then exits the app:
- The job may still be in `active` status (status=1) if they didn't accept.
- But the employee may not see it again in their job list because `jobAlert()` doesn't re-notify them.
- The `employee_joblist()` may not include jobs that were previously shown via notification.

**Backend Fix Applied:**

1. **New endpoint `POST /api/active-job`** (`job_views.active_job`) - session restoration. No parameters, auth token only. Returns:
   ```json
   {"success":1,"message":"Active job fetched",
    "data":{"has_active_job":1,
            "active_job":{"job_id":5,"job_state":"pending","can_accept":1,
                          "notificationScreenType":"addjob","job_status":"active",
                          "client_name":"...","images":[...], "...":"same fields as /api/job_details"}}}
   ```
   - When nothing is open: `{"has_active_job":0,"active_job":null}` with `success:1`.
   - **Employee:** first the job they accepted and have not completed (`job_state: "in_progress"`), otherwise the newest active job they were alerted about and have not accepted/rejected (`job_state: "pending"`).
   - **Client:** their own job that is still waiting for an employee or in progress.
   - Jobs cancelled by the client (status 4), completed (3) or with no availability (5) are never returned.

2. **Notification state is now read back from the `Alerts` table.** `jobAlert()` already persists the notified employee list per job; `was_alerted()` uses it, so dismissing/clearing the push notification no longer loses the job - the employee gets it back from `/api/active-job` and from the job list. Jobs with no `Alerts` row (legacy) stay visible to all employees.

3. **`employee_joblist()`** now returns every active job the employee has not rejected/cancelled (not just newly notified ones), ordered newest-first for stable pagination, plus per-job flags so the app knows which buttons to show:
   - `can_accept` (1/0) - job is active and this employee has not acted on it → show Accept/Decline.
   - `is_assigned` (1/0) - this employee is the acceptor → show in-progress/directions screen.
   - `was_notified` (1/0) - this employee was alerted about the job.
   - `job_status` now reports `"Not accepted"` for status 5 instead of mislabelling it `"cancelled"`; `total_records` added to the response.

4. `job_details()` and `active_job()` share one `build_job_payload()` helper, so both return the identical job shape (including before/after images).

**Frontend follow-up:** call `/api/active-job` on app launch/resume and route on `job_state`; treat `has_active_job:0` as "nothing pending". Preventing the *dismissal* of the notification itself is still frontend work - the backend now guarantees the job can always be recovered.

---

## Issues That Are Primarily Frontend (Mobile App)


| Issue | Description | Backend Needed? |
|-------|-------------|-----------------|
| **Camera Access Protocol** | Allow camera access through settings or popup prompt | **No** - This is 100% mobile app permission handling (AndroidManifest.xml / iOS Info.plist) |
| **Service Distance (21 min)** | Was fixed but broke in later APKs | **Verify only** - Backend already has the 21-minute logic in `jobAlert()` using Google Distance Matrix API. The issue is likely in the mobile app's GPS/location handling. |
| **Password Visibility Toggle** | Hidden/shown password option | **No** - Purely frontend UI |
| **Yes/No Instead of On/Off** | Job detail question toggles | **No** - Purely frontend UI |

---

## Payment Gateway Analysis

| Gateway | Backend Status | Notes |
|---------|---------------|-------|
| **Stripe** | Implemented | Full integration exists in `payment.py`, `stripe.py`, `payment_views.py` |
| **PayPal** | Implemented | Full integration in `background_paypal.py`, `paypal_first_payment.py`, `paypal_views.py` |
| **Apple Pay** | Partial | Stub exists in `apple_pay.py` and `payment_views.py` - creates Stripe PaymentIntent for Apple Pay on iOS |
| **Venmo** | Not implemented | No code exists |
| **Zelle** | Not implemented | No code exists |

**Note:** The user has deferred Venmo/Zelle integration. Apple Pay backend exists but may need testing.

---



## Known Backend Bugs Found During Analysis

| Bug | File | Severity |
|-----|------|----------|
| `reject_job()` is a stub - does nothing | `job_views.py:1046` | **Critical** |
| `PaymentFailedInfo` serializer has `Meta.model = Feedback` (wrong model) | `serializers.py` | **Medium** |
| Plaintext passwords stored in `SweetWord` table | `models.py` | **Security** |
| Google Maps API key hardcoded in source | `job_views.py` | **Security** |
| FCM private key hardcoded in source | `fcm.py` | **Security** |
| No API endpoint to check for active/in-progress job for an employee | - | **Functional** |
| No job history endpoint with images | - | **Functional** |
| `Alerts` model is written to but never exposed via API | - | **Functional** |

---

## Priority Backend Tasks

1. **[Critical]** Implement `reject_job()` properly - track rejections, handle "all rejected" scenario
2. **[Critical]** Fix job cancellation visibility - ensure canceled jobs disappear immediately from employee lists
3. **[Critical]** Fix notification consolidation for job completion (one notification, auto review page)
4. **[High]** Create `/api/job-history` endpoint with images
5. **[High]** Create `/api/active-job` endpoint for job session restoration
6. **[High]** Add `no_availability` notificationScreenType for issues 5 & 6
7. **[Medium]** Improve error handling in `cancel_job_by_employee()`
8. **[Medium]** Fix `PaymentFailedInfo` serializer bug
9. **[Medium]** Verify 21-minute distance logic works end-to-end
10. **[Low]** Remove hardcoded API keys and secrets from source code

---

## Conclusion

The majority of the reported issues (9 out of 14) require backend changes. The most critical issues are:

- **`reject_job()` being a non-functional stub** - this cascades into multiple reported problems
- **Missing job history and active-job endpoints** - causing images not to show and job session loss
- **Notification payload not signaling the frontend properly** - causing review page and availability message issues
- **Job cancellation not propagating in real-time** - causing canceled jobs to remain visible

The frontend team should coordinate with backend changes, particularly for:
- New `notificationScreenType` values in FCM payloads
- New API endpoints (`/api/job-history`, `/api/active-job`)
- Modified `employee_joblist()` response format
