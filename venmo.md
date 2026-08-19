# Venmo — Integration Status

**Venmo is now implemented in this backend**, mirroring the working PayPal
card-vault flow. It's processed through PayPal's Orders API
(`payment_source.venmo`) — no separate Braintree SDK.

| Method | Path | View | Purpose |
|---|---|---|---|
| POST | `create-venmo-order` | `venmo_views.create_venmo_order` | Create a Venmo order (`/v2/checkout/orders`), returns the `payer-action` approval link |
| POST | `capture-venmo-order` | `venmo_views.capture_venmo_order` | Capture an approved order, persist vault info if requested, mark the job paid |

New model: `VenmoInfo` (`openup_app/models.py`, table `venmo_cust_info`,
migration `openup_app/migrations/0062_venmoinfo.py`) — mirrors `PaypalInfo`
(vault id, customer id, email, raw response). `add_payment_type` now also
accepts `payment_type=venmo`.

New config, staged in `openup/.env_example`: `PAYPAL_BASE_URL`,
`PAYPAL_BRAND_NAME`, `VENMO_RETURN_URL`, `VENMO_CANCEL_URL` (the latter two
were already present locally but unused/undocumented before this change).

The reference material below (PayPal's Orders API spec) is what the
implementation above follows.

## What currently exists (working today)

| Method | Path | View | Purpose |
|---|---|---|---|
| POST | `create-paypal-customer` | `paypal_views.create_customer` | Create a PayPal vault customer |
| POST | `paypal-payment` | `paypal_views.paypal_payment` | Card-based PayPal payment |
| POST | `payment-type` | `paypal_views.add_payment_type` | Add/save a payment method (`stripe`, `paypal`, `apple_pay`) |
| POST | `paypal-payment-token-receiver` | `paypal_views.paypal_payment_token_receiver` | Receive vault payment token |
| POST | `apple-pay` | `apple_pay_views.apple_pay` | Apple Pay payment |
| POST | `create-webhook` | `paypal_views.create_webhook` | Register PayPal webhook |
| POST | `webhook-data` | `paypal_views.receive_webhook_data` | Receive PayPal webhook events |
| POST | `create-paypal-token` | `paypal_views.create_paypal_token` | Create PayPal setup token |

These implement a **PayPal card-vault** flow (`/v3/vault/setup-tokens`,
`/v3/vault/payment-tokens`), plus Stripe and Apple Pay.

Config read by this code (`openup_api/views/paypal_views.py`,
`payment_views.py`, `venmo_views.py`): `CLIENT_ID`, `CLIENT_SECRET`
(PayPal app credentials), plus the new `PAYPAL_BASE_URL`, `PAYPAL_BRAND_NAME`,
`VENMO_RETURN_URL`, `VENMO_CANCEL_URL` now read by `venmo_views.py` and staged
in `openup/.env_example`.

## Implementation notes

PayPal natively brokers Venmo through its own **Orders/Checkout API** — no
separate Braintree SDK is needed. Commented-out dead code in
`paypal_views.py` and `payment_views.py` already sketches the relevant shape
via `payment_source.paypal`, which Venmo would mirror as `payment_source.venmo`:

```json
{
  "intent": "CAPTURE",
  "purchase_units": [
    { "amount": { "currency_code": "USD", "value": "100.00" } }
  ],
  "payment_source": {
    "venmo": {
      "experience_context": {
        "brand_name": "YourBrandName",
        "return_url": "https://.../return",
        "cancel_url": "https://.../cancel"
      }
    }
  }
}
```

The frontend will need:
- A "Pay with Venmo" button that hits `create-venmo-order`, then follows the
  returned `payer-action` link so the payer can approve in Venmo.
- Redirect handling for the `VENMO_RETURN_URL` / `VENMO_CANCEL_URL` deep
  links configured via `experience_context`.
- A call to `capture-venmo-order` with the order ID after the redirect back,
  similar to the existing PayPal order flow.

---

## Reference: PayPal's actual Venmo API (external)

This is PayPal's own REST API for Venmo (Venmo is processed *through* PayPal's
Orders API via `payment_source.venmo` — no separate Braintree SDK). Use this
as the spec for whatever backend endpoints eventually get built, and as the
target shape the frontend should plan around.

### 0. Auth (reuses existing PayPal setup)

Same OAuth pattern already used for the working PayPal card-vault flow in
`openup_api/views/paypal_views.py` — get a bearer token from `CLIENT_ID` /
`CLIENT_SECRET`:

```
POST https://api-m.sandbox.paypal.com/v1/oauth2/token
Authorization: Basic base64(CLIENT_ID:CLIENT_SECRET)
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
```
→ returns `access_token`, used as `Authorization: Bearer <access_token>` on every call below.

### 1. Create Order — `POST /v2/checkout/orders`

**Headers:** `Authorization: Bearer <access_token>`, `Content-Type: application/json`, optionally `PayPal-Request-Id` (idempotency key).

**Request body (one-time payment):**
```json
{
  "intent": "CAPTURE",
  "purchase_units": [
    {
      "amount": { "currency_code": "USD", "value": "100.00" }
    }
  ],
  "payment_source": {
    "venmo": {
      "email_address": "payer@example.com",
      "experience_context": {
        "brand_name": "EXAMPLE INC",
        "shipping_preference": "GET_FROM_FILE"
      }
    }
  }
}
```

**Request body (save Venmo account for future use — vaulting):**
```json
{
  "intent": "CAPTURE",
  "purchase_units": [
    { "amount": { "currency_code": "USD", "value": "100.00" } }
  ],
  "payment_source": {
    "venmo": {
      "email_address": "payer@example.com",
      "experience_context": {
        "brand_name": "EXAMPLE INC",
        "shipping_preference": "SET_PROVIDED_ADDRESS"
      },
      "attributes": {
        "vault": {
          "store_in_vault": "ON_SUCCESS",
          "usage_type": "PLATFORM"
        }
      }
    }
  }
}
```

**Response:**
```json
{
  "id": "ORDER-ID",
  "status": "PAYER_ACTION_REQUIRED",
  "payment_source": {
    "venmo": { "email_address": "payer@example.com" }
  },
  "links": [
    { "href": "https://api.sandbox.paypal.com/v2/checkout/orders/ORDER-ID", "rel": "self", "method": "GET" },
    { "href": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-ID", "rel": "payer-action", "method": "GET" }
  ]
}
```

**What the frontend needs to do with this response:**
- Pull the `id` (order ID) and hold onto it — it's needed for the capture step.
- Follow (or open a webview/browser to) the `payer-action` link so the payer
  can approve the payment in Venmo. On mobile this is where the deep link
  round-trip matters — after approval, Venmo/PayPal redirects back using the
  `return_url` / `cancel_url` configured in `experience_context` (this is
  exactly what the two currently-unused `VENMO_RETURN_URL` /
  `VENMO_CANCEL_URL` env vars were staged for).

### 2. Capture Order — `POST /v2/checkout/orders/{order_id}/capture`

**Headers:** same as above (`Authorization`, `Content-Type`).

**Request body:** `{}` (empty — order ID is in the URL).

**Response (vaulted case shown — includes reusable vault id):**
```json
{
  "id": "ORDER-ID",
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
  }
}
```

For non-vaulted payments, the same `COMPLETED` status and `purchase_units[].payments.captures[]`
block (amount, capture id, status) is returned without the `attributes.vault` object.

**What the frontend needs to do with this response:**
- Check `status == "COMPLETED"` to confirm success.
- If vaulting was requested, the backend should persist
  `payment_source.venmo.attributes.vault.id` and `...customer.id` (mirrors
  how `PaypalInfo` already stores vault/customer IDs today) so the payer
  doesn't have to re-authorize Venmo on their next payment.

### Field reference — `payment_source.venmo`

| Field | Required | Notes |
|---|---|---|
| `email_address` | optional | Pre-fills/identifies the Venmo payer if known |
| `experience_context.brand_name` | recommended | Shown to payer during approval |
| `experience_context.shipping_preference` | optional | `GET_FROM_FILE` / `SET_PROVIDED_ADDRESS` / `NO_SHIPPING` |
| `attributes.vault.store_in_vault` | optional | `ON_SUCCESS` to save the Venmo account for reuse |
| `attributes.vault.usage_type` | optional, required if vaulting | `PLATFORM` or `MERCHANT` |

### Config the backend will need to add

- `PAYPAL_BASE_URL` — `https://api-m.sandbox.paypal.com` (sandbox) vs `https://api-m.paypal.com` (prod). Currently hardcoded to sandbox in `paypal_views.py`/`payment_views.py`; the `.env` var of this name exists but isn't read yet.
- `PAYPAL_BRAND_NAME` — sent as `experience_context.brand_name`. Also staged in `.env` but unread.
- `VENMO_RETURN_URL` / `VENMO_CANCEL_URL` — deep links the frontend/mobile app redirects to after Venmo approval/cancellation. Already in `.env`, unread.
- `CLIENT_ID` / `CLIENT_SECRET` — already used for PayPal today, same app credentials work for Venmo since it's the same PayPal platform.

**Sources:**
- [Save Venmo with the JavaScript SDK — PayPal Developer](https://developer.paypal.com/docs/multiparty/checkout/save-payment-methods/during-purchase/js-sdk/venmo/)
- [PayPal Checkout standard use case — Orders API](https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/standard)
- [Orders v2 API reference](https://developer.paypal.com/docs/api/orders/v2/)
