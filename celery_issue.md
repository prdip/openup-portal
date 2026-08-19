# Celery — Issues Found & Changes Needed

Investigated the actual Celery setup (config, worker process, task
registry) rather than just reading source — findings below are backed by
live checks (`celery inspect registered`, a running worker, `redis-cli
ping`), not assumptions. **No code was changed to produce this document.**

## Current setup (for context)

- Broker + config: `openup/celery.py`, `app.config_from_object('django.conf:settings', namespace='CELERY')`
- Settings: `openup/settings.py:49-55`
- A worker **is** currently running (`celery -A openup.celery worker -l INFO`, 5 processes, confirmed via `ps aux`)
- Redis **is** reachable (`redis-cli ping` → `PONG`)
- `django_celery_results` migrations are applied
- `celery -A openup.celery inspect registered` confirms which tasks the running worker actually knows about (see below) — this is hard evidence, not guesswork

---

## Issue 1: Four job-notification tasks were converted from async to synchronous, even though a working worker is available

**File:** `openup_api/views/job_views.py`

`accept_job_notification`, `complete_job_notification`,
`cancel_job_notification`, and `notify_client` all have their
`@shared_task()` decorator **commented out** (lines 1233, 1472, 1598, 1895),
and every call site that used to dispatch them via `.delay(...)` is also
commented out, replaced with a direct synchronous call:

```python
# accept_job_notification.delay(job_id)   <- commented out
accept_job_notification(job_id)            <- calls the function directly instead
```
(same pattern at the `complete_job_notification`, `cancel_job_notification`,
and `notify_client` call sites)

**Confirmed via the live worker's task registry** — these four are simply
absent:
```
celery -A openup.celery inspect registered
  * openup.celery.debug_task
  * openup_api.views.auth_views.send_change_password_email
  * openup_api.views.auth_views.send_email
  * openup_api.views.auth_views.send_forget_pass_email
  * openup_api.views.job_views.background_payment
  * openup_api.views.job_views.job_alert_after_cancel
  * openup_api.views.job_views.paypal_payment
  * openup_api.views.payment_views.background_payment
  * openup_api.views.payment_views.paypal_payment
  * openup_api.views.payment_views.send_notification
  * openup_api.views.paypal_views.background_payment
  * openup_api.views.paypal_views.create_customer
  * openup_api.views.paypal_views.first_payment
  * openup_api.views.vehicle_views.create_customer
```
No `accept_job_notification` / `complete_job_notification` /
`cancel_job_notification` / `notify_client` in that list — they are plain
Python functions right now, not Celery tasks.

**Why this matters:** every other background job in the codebase (payments,
paypal, emails — see the list above) is still dispatched correctly via
`@shared_task()` + `.delay()`, and the worker is actively running and able
to process them. These four are the only inconsistent ones. Since they're
now called directly, `accept_job`, `complete_job`, `cancel_job`, and
`cancel_job_by_employee` all block their HTTP request/response on an FCM
push + (for `notify_client`) a Distance Matrix API search, instead of
returning immediately and letting the already-running worker handle it in
the background — despite the infrastructure to do that being fully
operational.

**Change needed:** uncomment the four `@shared_task()` decorators and
restore the `.delay(...)` calls at each call site.

---

## Issue 2: Dead task still registered with the worker

**File:** `openup_api/views/job_views.py`

`job_alert_after_cancel` (line ~1816) still has an **active**
`@shared_task()` decorator, and is confirmed registered with the worker
(`openup_api.views.job_views.job_alert_after_cancel` appears in the
registry above) — but it has **no call sites anywhere** in the codebase
(confirmed by search). It's a fully dead, duplicate copy of `jobAlert`'s
logic that happens to still be wired up to Celery while the four functions
that actually need to be async (issue 1) aren't.

**Change needed:** delete the function (it's unreachable dead code), which
also removes it from the task registry.

---

## Issue 3: Broker URL is hardcoded to localhost, and an env var read is silently discarded

**File:** `openup/settings.py:48-49`

```python
os.environ.get('REDIS_URL')                        # return value never used - does nothing
CELERY_BROKER_URL                   =       'redis://127.0.0.1:6379'
```

The `os.environ.get('REDIS_URL')` call looks like it was meant to feed
`CELERY_BROKER_URL`, but its result is never assigned anywhere — the next
line hardcodes `127.0.0.1:6379` regardless. In this dev environment that
happens to work because Redis is running locally, but in any deployment
where Redis isn't on `localhost:6379` (a managed Redis instance, a
different host in production, etc.), Celery will fail to connect to the
broker and **every** `.delay()` call across the app (payments, emails,
paypal — not just job notifications) will fail.

**Change needed:**
```python
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379')
```

---

## Issue 4: `CELERY_RESULT_BACKEND` is set twice, first value silently discarded

**File:** `openup/settings.py:50,54`

```python
CELERY_RESULT_BACKEND               =       'redis://127.0.0.1:6379'   # line 50 - dead, overwritten below
CELERY_ACCEPT_CONTENT               =       ['application/json']
CELERY_RESULT_SERIALIZER            =       'json'
CELERY_TASK_SERIALIZER              =       'json'
CELERY_RESULT_BACKEND               =       'django-db'                # line 54 - the value actually used
```
Not currently broken (the `django-db` backend is correctly installed via
`django_celery_results` in `INSTALLED_APPS`, and its migrations are
applied), but the redundant/dead line-50 assignment is confusing and reads
as if results go to Redis when they actually go to the database.

**Change needed:** delete the dead `CELERY_RESULT_BACKEND = 'redis://...'`
line at 50.

---

## Issue 5: The same task logic is duplicated across multiple files

**Files:** `openup_api/views/job_views.py`, `openup_api/views/payment_views.py`, `openup_api/views/paypal_views.py`, `openup_api/views/vehicle_views.py`

The task registry shows the same task names defined independently in
multiple modules, each registered as a **separate** task under its own
fully-qualified name:
- `background_payment` — defined in `job_views.py`, `payment_views.py`, **and** `paypal_views.py` (3 copies)
- `paypal_payment` — defined in `job_views.py` **and** `payment_views.py` (2 copies)
- `create_customer` — defined in `paypal_views.py` **and** `vehicle_views.py` (2 copies)

These aren't name collisions (Celery namespaces them by full module path),
but three independently-maintained copies of "the same" payment task is a
correctness risk — a fix applied to one copy silently doesn't apply to the
other two, and it's not obvious from a call site which copy is actually
being invoked without checking the import.

**Change needed:** consolidate each into a single shared implementation
(e.g. move to a dedicated `tasks.py` and import it everywhere it's used)
rather than three independently-drifting copies.

---

## Issue 6: Two requirements files with different pinned Celery versions

**Files:** `requirements.txt`, `requirement.txt`

```
requirements.txt:  celery==5.4.0   kombu==5.6.2
requirement.txt:   celery==5.3.6   kombu==5.3.5
```
`requirement.txt` (no "s") isn't referenced by any script or doc in the
repo — it looks like a stray duplicate, but if anyone runs
`pip install -r requirement.txt` by habit/typo, they'll provision a
different Celery/Kombu version than what's actually developed against.

**Change needed:** delete `requirement.txt`, or if it serves a real purpose,
rename it and keep both dependency lists in sync deliberately.

---

## Issue 7: No process supervision for the worker — it's a manual command only

**File:** `commands.md` (only place the worker start command is documented)

```
celery -A openup.celery worker -l INFO
```
This is the **only** place the worker is started from — there's no
systemd unit, supervisor config, Docker service, or `Procfile` managing it.
There's also no `CELERY_TASK_ALWAYS_EAGER` fallback configured, so if the
worker process isn't running, every `.delay()` call across the entire app
(not just job notifications) silently queues in Redis and is never
processed, with nothing in the request/response cycle indicating failure.
This is plausibly *why* issue 1 happened — if the worker wasn't running
during testing at some point, the job-notification tasks would have looked
"broken," and the fix applied was to bypass Celery for those four instead
of ensuring the worker stays up.

**Change needed:** run the worker under a process supervisor (systemd
service, supervisord, or equivalent) that restarts it if it dies, so async
tasks reliably get processed without needing anyone to remember to start it
manually.
