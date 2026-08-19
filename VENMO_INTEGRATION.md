# Venmo Integration — Backend & Frontend Contract

**Date:** July 2026
**Status:** Backend implemented, needs a Venmo-enabled live PayPal account to go live
**Scope:** Venmo as a fourth payment method alongside Stripe, PayPal (card) and Apple Pay

---

## 1. Why Venmo is not "just another PayPal card"

The existing PayPal flow is a **card vault**: the app posts a card number to `/api/payment-type`, the backend vaults it, and every job after that is charged server-side with no user interaction.

**Venmo has no card number.** The buyer must approve the account inside the Venmo app. So saving a Venmo account takes **two calls with an app-switch in between**:

```
  App                        Backend                     PayPal / Venmo
   │                            │                             │
   │  POST /api/venmo-setup     │                             │
   ├───────────────────────────►│  create setup token         │
   │                            ├────────────────────────────►│
   │  { approval_url }          │  { id, links[payer-action] } │
   │◄───────────────────────────┤◄────────────────────────────┤
   │                            │                             │
   │  open approval_url ─────────────────────────────────────►│  buyer approves
   │                            │                             │  in Venmo app
   │  ◄─── returns to return_url ────────────────────────────┤
   │                            │                             │
   │  POST /api/venmo-confirm   │                             │
   ├───────────────────────────►│  exchange for vault id      │
   │                            ├────────────────────────────►│
   │  { success: 1 }            │  { id: VAULT_ID }           │
   │◄───────────────────────────┤◄────────────────────────────┤
   │                            │  saves PaypalInfo(venmo)    │
   │                            │  sets user_payment_type     │
```

**After this one-time setup, nothing else changes.** `POST /api/add_job` with `payment_type: "venmo"` charges the vaulted account in the background exactly like the card flow — no app-switch, no approval, no extra screens.

---

## 2. Frontend payload changes

### 2.1 `POST /api/venmo-setup` — NEW

Starts the Venmo linking. Nothing is saved yet; an unapproved setup token cannot be charged.

**Request**

| Field | Required | Notes |
|---|---|---|
| `return_url` | yes | Your deep link, e.g. `openup://venmo/success`. Venmo sends the buyer here after approval. |
| `cancel_url` | yes | Deep link for "buyer backed out", e.g. `openup://venmo/cancel` |
| `paypal_req_id` | no | Idempotency key. Backend generates a UUID if omitted. |

```json
{ "return_url": "openup://venmo/success", "cancel_url": "openup://venmo/cancel" }
```

**Response**

```json
{
  "success": 1,
  "message": "Approve the venmo account to continue",
  "data": {
    "setup_token": "8kk8451t",
    "approval_url": "https://www.sandbox.paypal.com/agreements/approve?ba_token=..."
  }
}
```

The app **must open `approval_url`** (app-switch to Venmo, or the in-app browser) and **hold on to `setup_token`** — it is needed for step 2.

Failure cases: `success: 0` with `"Please provide return_url and cancel_url"`, `"Could not reach paypal, please try again"`, or `"Venmo is not available on this account right now"` (Venmo not enabled on the merchant account).

### 2.2 `POST /api/venmo-confirm` — NEW

Call this when the buyer lands back on your `return_url`.

**Request**

| Field | Required | Notes |
|---|---|---|
| `setup_token` | yes | The value from step 1 |
| `paypal_req_id` | no | Idempotency key |

```json
{ "setup_token": "8kk8451t" }
```

**Response**

```json
{
  "success": 1,
  "message": "Venmo account saved successfully",
  "data": { "payment_type": "venmo", "vault_id": "9pv84512cd" }
}
```

Only on `success: 1` is the account usable. This call is what flips `user_payment_type` to `venmo` — if the buyer abandons the approval, the user's previous payment method stays active.

### 2.3 `POST /api/payment-type` — CHANGED

`payment_type` now accepts `"venmo"` as a fourth value (`stripe`, `paypal`, `apple_pay`, `venmo`).

**When `payment_type: "venmo"`, this endpoint behaves like `/api/venmo-setup`** — same `return_url`/`cancel_url` inputs, same `{setup_token, approval_url}` response — and you still have to call `/api/venmo-confirm` afterwards. It does **not** return `"Payment method added successfully"` like the other methods do, because at that point nothing has been saved yet.

Use whichever endpoint fits your screen flow; they are the same code path. **Nothing changes for `stripe`, `paypal` or `apple_pay`.**

### 2.4 `POST /api/add_job` — CHANGED

Send `payment_type: "venmo"` exactly as you send `"paypal"` today. **No new fields.**

```json
{ "job_type": "service", "latitude": 22.26, "longitude": 70.78,
  "payment_type": "venmo", "paypal_req_id": "<uuid>", "year": "2019", "model": "T", ... }
```

The backend looks up the vaulted Venmo account and charges it in a background task. Emergency jobs that replay the last payment method also handle `venmo`.

### 2.5 Everything else — UNCHANGED

`/api/paypal-payment`, `/api/create-paypal-customer`, `/api/apple-pay`, `/api/add_card`, job endpoints: no payload changes. One behaviour fix worth knowing: **`/api/paypal-payment` used to return a 500** (it read the Python `id` builtin instead of the job id). It now returns proper JSON, so an error you may have been treating as "server down" will start coming back as a real response.

---

## 3. Mobile app work required

The backend cannot do these:

1. **Deep links** — register `return_url` / `cancel_url` schemes (or universal links) and route them to a handler that calls `/api/venmo-confirm`.
2. **iOS** — add `venmo` to `LSApplicationQueriesSchemes` in `Info.plist`, otherwise the app-switch silently fails.
3. **Android** — intent filter for the return scheme.
4. **UI** — a Venmo option in the payment picker; hide it for non-US users (Venmo is US-only).
5. **Pending state** — the buyer may never come back from the Venmo app. Don't leave the UI stuck; treat "no return within N seconds" as cancelled and let them retry.

Opening `approval_url` in a plain WebView often fails to app-switch. Use the platform browser (`SFSafariViewController` / Custom Tabs) or the PayPal/Braintree mobile SDK.

---

## 4. Configuration

New keys in `.env` (all optional — defaults preserve today's behaviour):

| Key | Default | Purpose |
|---|---|---|
| `PAYPAL_BASE_URL` | `https://api-m.sandbox.paypal.com` | The API host was hardcoded as sandbox in 15 places; it is now one setting. Switch to `https://api-m.paypal.com` for live. |
| `PAYPAL_WEBHOOK_ID` | *(empty)* | From the PayPal dashboard. **Until set, capture webhooks are stored but never change `job_pay_status`.** |
| `PAYPAL_BRAND_NAME` | `OpenUp` | Shown to the buyer in the Venmo approval screen |
| `VENMO_RETURN_URL` / `VENMO_CANCEL_URL` | *(empty)* | Fallback deep links when the app doesn't send its own |
| `JOB_AMOUNT_USD` / `JOB_CURRENCY` | `100.00` / `USD` | The per-job amount, previously hardcoded in the payloads |

**PayPal account prerequisites:** Venmo must be enabled on the live merchant account (PayPal has to approve it), US merchant, US buyer, USD only. Venmo is not fully testable in sandbox — plan for a live smoke test with a real Venmo account.

---

## 5. Backend changes

| File | Change |
|---|---|
| `openup/paypal_api.py` | **New.** `paypal_url()`, `get_access_token()`, `get_vault_record()`, `approval_link()`, `verify_webhook()` |
| `openup_api/views/venmo_views.py` | **New.** `venmo_setup`, `venmo_confirm`, `venmo_payment` task, `start_venmo_setup` helper |
| `openup_app/models.py` | `PaypalInfo.paypal_source_type` (`card` / `venmo` / `paypal`), migration `0061` |
| `openup_api/views/paypal_views.py` | `add_payment_type` accepts `venmo`; vault lookup is source-aware; `paypal_payment` `id`-builtin bug fixed; webhook now applies capture events |
| `openup_api/views/job_views.py` | `add_job` routes `venmo` (normal + emergency replay); vault lookup is source-aware; missing vault no longer crashes the task |
| `openup/background_paypal.py` | `pay_type` is parameterised so Venmo isn't logged as PayPal |
| `openup_api/urls.py` | `/api/venmo-setup`, `/api/venmo-confirm` |

### Why `PaypalInfo` and not a new table

`user_payment_type` on `Registration` says **which** gateway to charge — `add_job` already reads it. `PaypalInfo` holds the **credential**. A Venmo vault id is a PayPal vault id from the same `/v3/vault/payment-tokens` endpoint, so it belongs in the same table; it only needed a column to distinguish it from a card.

This also fixed a latent bug: every lookup was `PaypalInfo.objects.filter(paypal_user=user).first()` — whatever row the DB returned first. Once a user has both a card and Venmo vaulted, that charges the wrong instrument. Lookups now filter on source type and take the newest row.

---

## 6. Payment status correctness

The old card flow marked a job paid **before** the gateway responded. Cards nearly always succeed synchronously so this rarely showed. **Venmo can be approved by the buyer and denied afterwards**, so that assumption breaks.

Now:
- `job_pay_status` is set by `PaypalPayment.background_payments` only after PayPal accepts the order.
- `PAYMENT.CAPTURE.COMPLETED` → job paid, capture id stored in `job_payment_id`.
- `PAYMENT.CAPTURE.DENIED` / `DECLINED` / `REVERSED` → job un-paid, `PaymentFailedInfo` row written.
- The job id travels as `custom_id` on the purchase unit, which is how the webhook matches the job.
- **Events are only acted on when PayPal verifies the signature.** Without `PAYPAL_WEBHOOK_ID` the payload is stored and ignored — otherwise anyone who knows the webhook URL could mark jobs as paid.

---

## 7. Test status

22 assertions across the Venmo flow and 12 regression assertions on the existing card flow pass against the dev database (PayPal HTTP mocked, all writes rolled back — `Jobs` and `PaypalInfo` counts unchanged):

- setup → approval link returned, payment type **not** switched yet
- confirm → vault stored as `venmo`, `user_payment_type` becomes `venmo`
- vault lookup returns the right instrument when both card and Venmo exist, and does **not** fall back across sources
- charge builds `payment_source.venmo.vault_id` with `custom_id` = job id, marks the job paid, logs `pay_type: "venmo"`
- missing vault → job left unpaid, `no_vault` failure recorded, no crash
- `add_payment_type` still rejects invalid types and still demands a card number for `paypal`
- webhook: unverified → stored only; verified COMPLETED → paid; verified DENIED → un-paid; bad signature → ignored
- existing card vaulting, card charging and `/api/active-job` all still behave as before

**Not tested against real PayPal.** The request/response shapes for the Venmo setup-token payload follow PayPal's vault-without-purchase flow, but the exact field set should be confirmed against current PayPal docs during the first sandbox call — the code handles both `payer-action` and `approve` link names to absorb the most likely difference.

---

## 8. Remaining work

1. Enable Venmo on the live PayPal account and set `PAYPAL_BASE_URL` + `PAYPAL_WEBHOOK_ID`.
2. Mobile: deep links, `LSApplicationQueriesSchemes`, payment picker entry.
3. First live smoke test — confirm the setup-token payload is accepted and the approval link app-switches.
4. `JOB_AMOUNT_USD` is a flat 100.00 for every job, unchanged from before. If pricing should vary, that is a separate change across all four gateways (Stripe still charges `500*100` in **INR**, which does not match the PayPal payloads).
