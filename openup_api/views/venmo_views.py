# Venmo is processed through PayPal's Orders API via payment_source.venmo
# (no separate Braintree SDK). This mirrors the existing PayPal card-vault
# flow in paypal_views.py, using the same PayPal app credentials.

from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from django.utils import timezone
import requests
import json

from openup_api.views.auth_views import token_verification
from openup_app.serializers import JobsSerializer
from openup_app.models import Registration, VenmoInfo, PaymentFailedInfo, Jobs

import environ
env = environ.Env()
environ.Env.read_env()

client_id           = env("CLIENT_ID")
client_secret       = env("CLIENT_SECRET")
PAYPAL_BASE_URL     = env("PAYPAL_BASE_URL", default="https://api-m.sandbox.paypal.com")
PAYPAL_BRAND_NAME   = env("PAYPAL_BRAND_NAME", default="")
VENMO_RETURN_URL    = env("VENMO_RETURN_URL", default="")
VENMO_CANCEL_URL    = env("VENMO_CANCEL_URL", default="")


def _get_access_token(venmo_req_id):
    url     = f'{PAYPAL_BASE_URL}/v1/oauth2/token'
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    if venmo_req_id:
        headers['PayPal-Request-Id'] = venmo_req_id
    data    = {'grant_type': 'client_credentials'}
    auth    = (client_id, client_secret)
    response = requests.post(url, headers=headers, data=data, auth=auth)
    return response.json().get('access_token')


# CREATE A VENMO ORDER — PAYER APPROVES VIA THE RETURNED payer-action LINK,
# THEN THE FRONTEND CALLS capture_venmo_order WITH THE ORDER ID

@api_view(['POST'])
def create_venmo_order(request):
    token = request.headers.get('Authorization')
    if not token:
        return JsonResponse({"success": 2, "message": "Authorization header missing"})

    user_token = token.replace("Bearer", "").strip()
    check_user = token_verification(user_token)

    if check_user is None:
        return JsonResponse({"success": 2, "message": "Unauthorized User"})

    login_customer = check_user['session_user']
    user           = Registration.objects.exclude(user_is_delete=1).get(user_id=login_customer)

    job_id        = request.data.get('job_id')
    amount        = request.data.get('amount')
    currency_code = request.data.get('currency_code', 'USD')
    venmo_req_id  = request.data.get('venmo_req_id')
    email_address = request.data.get('email_address')
    save_venmo    = request.data.get('save_venmo', False)
    return_url    = request.data.get('return_url') or VENMO_RETURN_URL
    cancel_url    = request.data.get('cancel_url') or VENMO_CANCEL_URL

    if not amount:
        return JsonResponse({"success": 0, "message": "Amount is required"})

    access_token = _get_access_token(venmo_req_id)
    if not access_token:
        return JsonResponse({"success": 0, "message": "Unable to authenticate with PayPal"})

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token,
    }
    if venmo_req_id:
        headers['PayPal-Request-Id'] = venmo_req_id

    if not return_url or not cancel_url:
        return JsonResponse({"success": 0, "message": "return_url and cancel_url are required"})

    venmo_source = {
        "experience_context": {
            "brand_name": PAYPAL_BRAND_NAME,
            "return_url": return_url,
            "cancel_url": cancel_url,
        }
    }
    if email_address:
        venmo_source["email_address"] = email_address

    if save_venmo:
        venmo_source["attributes"] = {
            "vault": {
                "store_in_vault": "ON_SUCCESS",
                "usage_type": "PLATFORM",
            }
        }

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {"amount": {"currency_code": currency_code, "value": str(amount)}}
        ],
        "payment_source": {"venmo": venmo_source},
    }

    response  = requests.post(f'{PAYPAL_BASE_URL}/v2/checkout/orders', headers=headers, json=payload)
    resp_data = json.loads(response.text)

    if resp_data.get("name") in ("UNPROCESSABLE_ENTITY", "INVALID_REQUEST"):
        PaymentFailedInfo(
            user_id                =   user.user_id,
            job_id                 =   job_id or "",
            payment_fail_type      =   resp_data.get("name"),
            payment_fail_response  =   resp_data,
            payment_fail_message   =   resp_data.get("message"),
            created_at             =   timezone.now(),
        ).save()
        return JsonResponse({
            "success"   :   0,
            "message"   :   "Invalid request",
            "data"      :   resp_data,
        })

    return JsonResponse({
        "success"   :   1,
        "message"   :   "venmo order created",
        "data"      :   resp_data,
    })


# CAPTURE A VENMO ORDER AFTER THE PAYER APPROVES IT, SAVE VAULT INFO
# (IF REQUESTED) AND MARK THE JOB AS PAID

@api_view(['POST'])
def capture_venmo_order(request):
    token = request.headers.get('Authorization')
    if not token:
        return JsonResponse({"success": 2, "message": "Authorization header missing"})

    user_token = token.replace("Bearer", "").strip()
    check_user = token_verification(user_token)

    if check_user is None:
        return JsonResponse({"success": 2, "message": "Unauthorized User"})

    login_customer = check_user['session_user']
    user           = Registration.objects.exclude(user_is_delete=1).get(user_id=login_customer)

    order_id     = request.data.get('order_id')
    job_id       = request.data.get('job_id')
    venmo_req_id = request.data.get('venmo_req_id')

    if not order_id:
        return JsonResponse({"success": 0, "message": "order_id is required"})

    access_token = _get_access_token(venmo_req_id)
    if not access_token:
        return JsonResponse({"success": 0, "message": "Unable to authenticate with PayPal"})

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token,
    }

    response  = requests.post(f'{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture', headers=headers, json={})
    resp_data = json.loads(response.text)

    if resp_data.get("status") != "COMPLETED":
        PaymentFailedInfo(
            user_id                =   user.user_id,
            job_id                 =   job_id or "",
            payment_fail_type      =   resp_data.get("name"),
            payment_fail_response  =   resp_data,
            payment_fail_message   =   resp_data.get("message"),
            created_at             =   timezone.now(),
        ).save()
        return JsonResponse({
            "success"   :   0,
            "message"   :   "payment not completed",
            "data"      :   resp_data,
        })

    venmo_source = resp_data.get("payment_source", {}).get("venmo", {})
    vault        = venmo_source.get("attributes", {}).get("vault")

    if vault:
        VenmoInfo(
            venmo_user      =   user,
            venmo_vault_id  =   vault.get("id", ""),
            venmo_cust_id   =   vault.get("customer", {}).get("id", ""),
            venmo_email     =   venmo_source.get("email_address"),
            venmo_response  =   resp_data,
            is_delete       =   0,
            created_at      =   timezone.now(),
        ).save()

    if job_id:
        try:
            job_record = Jobs.objects.exclude(is_delete=1).get(job_id=int(job_id))
            update_payment_status = {
                "job_payment_id"    :   job_id,
                "job_pay_status"    :   1,
            }
            job_ser = JobsSerializer(instance=job_record, data=update_payment_status, partial=True)
            if job_ser.is_valid():
                job_ser.save()
        except Jobs.DoesNotExist:
            pass

    return JsonResponse({
        "success"   :   1,
        "message"   :   "payment success",
        "data"      :   resp_data,
    })
