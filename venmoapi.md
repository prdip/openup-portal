# Venmo APIs — Requests & Responses

Reflects the current code in `openup_api/views/venmo_views.py` and the
`payment_type=venmo` branch of `openup_api/views/paypal_views.py::add_payment_type`.
Base URL below matches `BASE_URL` in `openup/.env_example`
(`http://192.168.1.5:8000/api`) — swap for your environment.

All three endpoints require a session token from login, sent as:
```
Authorization: Bearer <session_token>
```
Missing/invalid token → `{"success": 2, "message": "Unauthorized User"}` (or
`"Authorization header missing"` if the header is absent entirely) on every
endpoint below; this case isn't repeated per-endpoint after this point.

---

## 1. Create Venmo order — `POST /create-venmo-order`

View: `venmo_views.create_venmo_order`. Creates a PayPal order with
`payment_source.venmo` and returns the `payer-action` link the app should
open so the payer can approve in Venmo.

### Request

| Field | Required | Notes |
|---|---|---|
| `amount` | yes | String/number, e.g. `"25.00"` |
| `currency_code` | no | Default `USD` |
| `job_id` | no | Attached to `PaymentFailedInfo` if the order create fails |
| `venmo_req_id` | no | Idempotency key, sent as `PayPal-Request-Id` |
| `email_address` | no | Pre-fills/identifies the Venmo payer if known |
| `save_venmo` | no | `true` to vault the Venmo account (`store_in_vault: ON_SUCCESS`, `usage_type: PLATFORM`) |

```bash
curl -X POST 'http://192.168.1.5:8000/api/create-venmo-order' \
  -H 'Authorization: Bearer <session_token>' \
  -H 'Content-Type: application/json' \
  -d '{
        "amount": "25.00",
        "currency_code": "USD",
        "job_id": "142",
        "venmo_req_id": "job-142-order-1",
        "email_address": "payer@example.com",
        "save_venmo": true
      }'
```

### Response — success (`success: 1`)

```json
{
  "success": 1,
  "message": "venmo order created",
  "data": {
    "id": "5O190127TN364715T",
    "status": "PAYER_ACTION_REQUIRED",
    "payment_source": {
      "venmo": { "email_address": "payer@example.com" }
    },
    "links": [
      {
        "href": "https://api.sandbox.paypal.com/v2/checkout/orders/5O190127TN364715T",
        "rel": "self",
        "method": "GET"
      },
      {
        "href": "https://www.sandbox.paypal.com/checkoutnow?token=5O190127TN364715T",
        "rel": "payer-action",
        "method": "GET"
      }
    ]
  }
}
```

The app should hold onto `data.id` (needed for capture) and open the
`payer-action` link (`rel: "payer-action"`) — the payer approves there, then
Venmo/PayPal redirects to `VENMO_RETURN_URL` / `VENMO_CANCEL_URL`.

### Response — missing amount (`success: 0`)

```json
{ "success": 0, "message": "Amount is required" }
```

### Response — PayPal rejects the order (`success: 0`)

A `PaymentFailedInfo` row is also saved in this case.

```json
{
  "success": 0,
  "message": "Invalid request",
  "data": {
    "name": "INVALID_REQUEST",
    "message": "Request is not well-formed, syntactically incorrect, or violates schema.",
    "debug_id": "d7a5c9f3e2b1a",
    "details": [
      {
        "field": "/purchase_units/0/amount/value",
        "issue": "MISSING_REQUIRED_PARAMETER"
      }
    ]
  }
}
```

---

## 2. Capture Venmo order — `POST /capture-venmo-order`

View: `venmo_views.capture_venmo_order`. Called after the payer approves via
the `payer-action` link. Captures funds, persists vault info if the order
was created with `save_venmo: true`, and marks the job as paid.

### Request

| Field | Required | Notes |
|---|---|---|
| `order_id` | yes | `data.id` returned by `create-venmo-order` |
| `job_id` | no | If present, sets `job_payment_id`/`job_pay_status=1` on that job |
| `venmo_req_id` | no | Idempotency key for the token request |

```bash
curl -X POST 'http://192.168.1.5:8000/api/capture-venmo-order' \
  -H 'Authorization: Bearer <session_token>' \
  -H 'Content-Type: application/json' \
  -d '{
        "order_id": "5O190127TN364715T",
        "job_id": "142",
        "venmo_req_id": "job-142-capture-1"
      }'
```

### Response — success, vaulted (`success: 1`)

`VenmoInfo` is saved (`venmo_vault_id`, `venmo_cust_id`, `venmo_email`,
`venmo_response`) when the response includes `attributes.vault`.

```json
{
  "success": 1,
  "message": "payment success",
  "data": {
    "id": "5O190127TN364715T",
    "status": "COMPLETED",
    "payment_source": {
      "venmo": {
        "email_address": "payer@example.com",
        "attributes": {
          "vault": {
            "id": "ckfmsf",
            "customer": { "id": "4029352050" },
            "status": "VAULTED"
          }
        }
      }
    },
    "purchase_units": [
      {
        "payments": {
          "captures": [
            {
              "id": "3C679366BB123456X",
              "status": "COMPLETED",
              "amount": { "currency_code": "USD", "value": "25.00" }
            }
          ]
        }
      }
    ]
  }
}
```

### Response — success, not vaulted (`success: 1`)

Same shape, minus `payment_source.venmo.attributes.vault` — no `VenmoInfo`
row is saved in this case.

### Response — missing order_id (`success: 0`)

```json
{ "success": 0, "message": "order_id is required" }
```

### Response — capture not completed (`success: 0`)

A `PaymentFailedInfo` row is also saved in this case (e.g. payer denied the
payment, order already captured/expired).

```json
{
  "success": 0,
  "message": "payment not completed",
  "data": {
    "name": "UNPROCESSABLE_ENTITY",
    "message": "The requested action could not be performed, semantically incorrect, or failed business validation.",
    "debug_id": "1d2e3f4a5b6c",
    "details": [
      { "issue": "ORDER_NOT_APPROVED" }
    ]
  }
}
```

---

## 3. Set payment type to Venmo — `POST /payment-type`

View: `paypal_views.add_payment_type`. Existing endpoint, now also accepts
`payment_type=venmo`. Unlike `paypal`, no `card_number` is required —
Venmo's own vaulting happens via `create-venmo-order` / `capture-venmo-order`
above, not at this step.

```bash
curl -X POST 'http://192.168.1.5:8000/api/payment-type' \
  -H 'Authorization: Bearer <session_token>' \
  -H 'Content-Type: application/json' \
  -d '{ "payment_type": "venmo" }'
```

### Response — success (`success: 1`)

```json
{
  "success": 1,
  "message": "Payment method added successfully",
  "data": "venmo"
}
```

### Response — invalid payment type (`success: 0`)

```json
{ "success": 0, "message": "please provide valid payment type" }
```

---

## Config required (`openup/.env_example`)

```
CLIENT_ID=              # existing PayPal app credentials, reused for Venmo
CLIENT_SECRET=
PAYPAL_BASE_URL='https://api-m.sandbox.paypal.com'
PAYPAL_BRAND_NAME='YourBrandName'
VENMO_RETURN_URL='https://example.com/returnUrl'
VENMO_CANCEL_URL='https://example.com/cancelUrl'
```
