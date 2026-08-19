# Venmo Payment API (Mobile Integration)

Venmo is processed through PayPal's Orders API (`payment_source.venmo`) — no separate
Braintree SDK, same PayPal app credentials as the card/PayPal flow.

## Server `.env` keys required

| Key | Required | Notes |
|---|---|---|
| `CLIENT_ID` | yes | PayPal REST app client id |
| `CLIENT_SECRET` | yes | PayPal REST app secret |
| `PAYPAL_BASE_URL` | yes (has default) | `https://api-m.sandbox.paypal.com` for testing, `https://api-m.paypal.com` for live |
| `PAYPAL_BRAND_NAME` | recommended | Shown to the user in the Venmo approval screen |
| `VENMO_RETURN_URL` | yes* | Fallback deep link PayPal redirects to after approval |
| `VENMO_CANCEL_URL` | yes* | Fallback deep link PayPal redirects to on cancel |

\* `VENMO_RETURN_URL` / `VENMO_CANCEL_URL` were empty in `.env`, which made PayPal
reject order creation (`INVALID_REQUEST`) because Venmo's `experience_context`
requires non-empty `return_url`/`cancel_url`. The endpoint now also accepts
`return_url`/`cancel_url` directly in the request body (mobile apps normally send
their own deep link scheme, e.g. `openupapp://venmo-return`), falling back to the
`.env` values only if the body doesn't provide them. **Set at least one of the two
(env fallback or per-request) before calling the API.**

## Endpoints

### 1. `POST /create-venmo-order`

Headers: `Authorization: Bearer <user_token>`

Body:
```json
{
  "job_id": 123,
  "amount": "25.00",
  "currency_code": "USD",
  "venmo_req_id": "optional-idempotency-key",
  "email_address": "optional buyer email",
  "save_venmo": false,
  "return_url": "openupapp://venmo-return",
  "cancel_url": "openupapp://venmo-cancel"
}
```

- `amount` is required.
- `return_url` / `cancel_url`: required unless `VENMO_RETURN_URL` / `VENMO_CANCEL_URL`
  are set in `.env`. Mobile app should pass its own deep link scheme here.
- Response `data.links` contains a `payer-action` URL — open it (in-app browser /
  Venmo app) so the user can approve the payment.

### 2. `POST /capture-venmo-order`

Headers: `Authorization: Bearer <user_token>`

Body:
```json
{
  "order_id": "<order id from create-venmo-order response>",
  "job_id": 123,
  "venmo_req_id": "optional-idempotency-key"
}
```

Call this after the user approves and the app is redirected back via `return_url`.
On success (`status: COMPLETED`) the job's `job_pay_status` is set to `1`, and if
`save_venmo` was used, the vault info is stored in `VenmoInfo`.

## Checklist before going live

1. Set `CLIENT_ID` / `CLIENT_SECRET` to the live PayPal app credentials.
2. Set `PAYPAL_BASE_URL=https://api-m.paypal.com`.
3. Set `VENMO_RETURN_URL` / `VENMO_CANCEL_URL` in `.env` (or have the mobile app
   always send `return_url`/`cancel_url` in the request body).
4. Set `PAYPAL_WEBHOOK_ID` if using webhook-based capture verification
   (see `paypal_views.py`).
