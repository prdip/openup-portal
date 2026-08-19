# Venmo is processed through PayPal's Orders API via payment_source.venmo
# (no separate Braintree SDK). This mirrors the existing PayPal card-vault
# flow in paypal_views.py, using the same PayPal app credentials.
'''
VENMO PAYMENTS (VIA PAYPAL).

VENMO IS NOT A CARD. THERE IS NO NUMBER TO POST, THE BUYER HAS TO APPROVE INSIDE
THE VENMO APP, SO SAVING A VENMO ACCOUNT TAKES TWO CALLS INSTEAD OF ONE:

    1. POST /api/venmo-setup    -> RETURNS AN APPROVAL LINK, APP OPENS IT
       (BUYER APPROVES IN THE VENMO APP AND IS SENT BACK TO return_url)
    2. POST /api/venmo-confirm  -> EXCHANGES THE APPROVED SETUP TOKEN FOR A VAULT ID

AFTER THAT IT BEHAVES EXACTLY LIKE THE VAULTED CARD FLOW: EVERY JOB IS CHARGED
SERVER SIDE WITH payment_source.venmo.vault_id AND NEEDS NO BUYER INTERACTION.

REQUIREMENTS ON THE PAYPAL SIDE: VENMO ENABLED ON THE LIVE MERCHANT ACCOUNT,
US MERCHANT, US BUYER, USD ONLY.
'''

from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from django.utils import timezone
import requests
import json

from openup_api.views.auth_views import token_verification
from openup_app.serializers import JobsSerializer
from openup_app.models import Registration, VenmoInfo, PaymentFailedInfo, Jobs

from openup_api.views.auth_views import token_verification

from openup_app.models import Registration, PaypalInfo, Jobs, PaymentFailedInfo
from openup_app.serializers import RegisterSerializer, JobsSerializer

from openup.paypal_api import paypal_url, get_access_token, approval_link, get_vault_record

from celery import shared_task

import requests
import json
import uuid
import logging

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
logger = logging.getLogger('django.request')


'''
AMOUNT CHARGED PER JOB. IT WAS HARDCODED AS "100.00" IN EVERY PAYPAL PAYLOAD, SO
THE DEFAULT KEEPS THAT EXACT VALUE AND IT CAN NOW BE MOVED WITHOUT A CODE CHANGE.
'''
JOB_AMOUNT      =   env('JOB_AMOUNT_USD', default='100.00')
JOB_CURRENCY    =   env('JOB_CURRENCY', default='USD')

BRAND_NAME      =   env('PAYPAL_BRAND_NAME', default='OpenUp')


'''
RETURN/CANCEL URLS THE VENMO APP SENDS THE BUYER BACK TO. THE MOBILE APP OWNS
THESE (THEY ARE ITS DEEP LINKS), SO THE REQUEST WINS OVER THE .env FALLBACK.
'''
def experience_urls(request):

    return_url  =   request.data.get('return_url') or env('VENMO_RETURN_URL', default='')
    cancel_url  =   request.data.get('cancel_url') or env('VENMO_CANCEL_URL', default='')

    return return_url, cancel_url


'''
STEP 1 - START SAVING A VENMO ACCOUNT.

RETURNS THE SETUP TOKEN AND THE LINK THE APP MUST OPEN SO THE BUYER CAN APPROVE.
NOTHING IS STORED YET: AN UNAPPROVED SETUP TOKEN CANNOT BE CHARGED.

SHARED WITH add_payment_type SO BOTH ENTRY POINTS BEHAVE IDENTICALLY.
'''
def start_venmo_setup(request, login_user):

    try:
        user    =   Registration.objects.exclude(user_is_delete=1).get(user_id=login_user)
    except Registration.DoesNotExist:
        return JsonResponse({"success": 0, "message": "Unauthorized User"})

    return_url, cancel_url  =   experience_urls(request)

    if return_url == '' or cancel_url == '':
        return JsonResponse({
            "success": 0,
            "message": "Please provide return_url and cancel_url",
        })

    paypal_req_id   =   request.data.get('paypal_req_id') or str(uuid.uuid4())

    access_token    =   get_access_token(paypal_req_id)
    if access_token is None:
        logger.error('venmo_setup: Could not get paypal access token for user %s', login_user)
        return JsonResponse({"success": 0, "message": "Could not reach paypal, please try again"})

    headers =   {
        'Content-Type'      :   'application/json',
        'PayPal-Request-Id' :   paypal_req_id,
        'Authorization'     :   'Bearer ' + access_token,
    }

    '''
    usage_type MERCHANT IS WHAT MAKES THE LATER CHARGES MERCHANT INITIATED, IE. THE
    BUYER DOES NOT HAVE TO BE IN THE APP WHEN A JOB IS PAID FOR.
    '''
    payload =   {
        "payment_source": {
            "venmo": {
                "usage_type"    :   "MERCHANT",
                "customer_type" :   "CONSUMER",
                "experience_context": {
                    "brand_name"    :   BRAND_NAME,
                    "locale"        :   "en-US",
                    "return_url"    :   return_url,
                    "cancel_url"    :   cancel_url,
                }
            }
        }
    }

    try:
        response    =   requests.post(paypal_url('/v3/vault/setup-tokens'), headers=headers, json=payload, timeout=30)
        resp_data   =   json.loads(response.text)
    except Exception as e:
        logger.error('venmo_setup: paypal call failed for user %s: %s', login_user, str(e))
        return JsonResponse({"success": 0, "message": "Could not reach paypal, please try again"})

    setup_token =   resp_data.get('id')
    approve_url =   approval_link(resp_data)

    if setup_token is None or approve_url is None:
        logger.error('venmo_setup: Unexpected paypal response for user %s: %s', login_user, resp_data)
        PaymentFailedInfo(
            user_id=user.user_id,
            job_id="",
            payment_fail_type=str(resp_data.get('name', 'venmo_setup_failed'))[:100],
            payment_fail_response=resp_data,
            created_at=timezone.now()
        ).save()
        return JsonResponse({
            "success": 0,
            "message": "Venmo is not available on this account right now",
            "data": resp_data,
        })

    return JsonResponse({
        "success": 1,
        "message": "Approve the venmo account to continue",
        "data": {
            "setup_token"   :   setup_token,
            "approval_url"  :   approve_url,
        }
    })


'''STEP 1 ENDPOINT - POST /api/venmo-setup'''
@api_view(['POST'])
def venmo_setup(request):

    token       =   request.headers.get('Authorization')
    if not token:
        return JsonResponse({"success": 0, "message": "Authorization header missing"})

    user_token  =   token.replace("Bearer", '').strip()
    check_user  =   token_verification(user_token)

    if check_user is None:
        return JsonResponse({"success": 0, "message": "Unauthorized User"})

    return start_venmo_setup(request, check_user['session_user'])


'''
STEP 2 - FINISH SAVING A VENMO ACCOUNT.

CALLED AFTER THE BUYER COMES BACK FROM THE VENMO APP. EXCHANGES THE APPROVED SETUP
TOKEN FOR A PERMANENT VAULT ID AND MAKES VENMO THE USER'S PAYMENT TYPE.
'''
@api_view(['POST'])
def venmo_confirm(request):

    token       =   request.headers.get('Authorization')
    if not token:
        return JsonResponse({"success": 0, "message": "Authorization header missing"})

    user_token  =   token.replace("Bearer", '').strip()
    check_user  =   token_verification(user_token)

    if check_user is None:
        return JsonResponse({"success": 0, "message": "Unauthorized User"})

    login_user  =   check_user['session_user']
    setup_token =   request.data.get('setup_token')

    if setup_token is None or setup_token == '':
        return JsonResponse({"success": 0, "message": "Please provide the setup_token"})

    try:
        user    =   Registration.objects.exclude(user_is_delete=1).get(user_id=login_user)
    except Registration.DoesNotExist:
        return JsonResponse({"success": 0, "message": "Unauthorized User"})

    paypal_req_id   =   request.data.get('paypal_req_id') or str(uuid.uuid4())

    access_token    =   get_access_token(paypal_req_id)
    if access_token is None:
        logger.error('venmo_confirm: Could not get paypal access token for user %s', login_user)
        return JsonResponse({"success": 0, "message": "Could not reach paypal, please try again"})

    headers =   {
        'Content-Type'      :   'application/json',
        'PayPal-Request-Id' :   paypal_req_id,
        'Authorization'     :   'Bearer ' + access_token,
    }

    '''SAME EXCHANGE THE VAULTED CARD FLOW DOES, ONLY THE SETUP TOKEN DIFFERS'''
    payload =   {
        "payment_source": {
            "token": {
                "id"    :   setup_token,
                "type"  :   "SETUP_TOKEN"
            }
        }
    }

    try:
        response    =   requests.post(paypal_url('/v3/vault/payment-tokens'), headers=headers, json=payload, timeout=30)
        resp_data   =   json.loads(response.text)
    except Exception as e:
        logger.error('venmo_confirm: paypal call failed for user %s: %s', login_user, str(e))
        return JsonResponse({"success": 0, "message": "Could not reach paypal, please try again"})

    vault_id    =   resp_data.get('id')

    if vault_id is None:
        logger.error('venmo_confirm: No vault id for user %s: %s', login_user, resp_data)
        PaymentFailedInfo(
            user_id=user.user_id,
            job_id="",
            payment_fail_type=str(resp_data.get('name', 'venmo_vault_failed'))[:100],
            payment_fail_response=resp_data,
            created_at=timezone.now()
        ).save()
        return JsonResponse({
            "success": 0,
            "message": "Could not save the venmo account, please approve it and try again",
            "data": resp_data,
        })

    try:
        cust_id =   resp_data["customer"]["id"]
    except (KeyError, TypeError):
        cust_id =   ""

    PaypalInfo(
        paypal_user         =   user,
        paypal_valut_id     =   vault_id,
        paypal_response     =   resp_data,
        paypal_cust_id      =   cust_id,
        paypal_source_type  =   "venmo",
        is_delete           =   0,
        created_at          =   timezone.now()
    ).save()

    '''ROUTES EVERY LATER JOB THROUGH VENMO - add_job READS THIS FIELD'''
    user_serializer =   RegisterSerializer(instance=user,data={"user_payment_type": "venmo"},partial=True)
    if user_serializer.is_valid():
        user_serializer.save()

    return JsonResponse({
        "success": 1,
        "message": "Venmo account saved successfully",
        "data": {
            "payment_type"  :   "venmo",
            "vault_id"      :   vault_id,
        }
    })


'''
CHARGES A JOB TO THE SAVED VENMO ACCOUNT. RUNS IN THE BACKGROUND EXACTLY LIKE THE
PAYPAL CARD TASK, AND MARKS THE JOB PAID ONLY WHEN PAYPAL ACCEPTS THE ORDER.
'''
@shared_task()
def venmo_payment(data):

    job_id          =   data['job_id']
    login_user      =   data['user']
    paypal_req_id   =   data.get('paypal_req_id') or str(uuid.uuid4())

    vault           =   get_vault_record(login_user,'venmo')

    if vault is None:
        logger.error('venmo_payment: No vaulted venmo account for user %s (job %s)', login_user, job_id)
        PaymentFailedInfo(
            user_id=login_user,
            job_id=job_id,
            payment_fail_type="no_vault",
            payment_fail_response="No vaulted venmo account found for this user",
            created_at=timezone.now()
        ).save()
        return False

    access_token    =   get_access_token(paypal_req_id)
    if access_token is None:
        logger.error('venmo_payment: Could not get paypal access token (job %s)', job_id)
        PaymentFailedInfo(
            user_id=login_user,
            job_id=job_id,
            payment_fail_type="token_failed",
            payment_fail_response="Could not get a paypal access token",
            created_at=timezone.now()
        ).save()
        return False

    payload =   {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id"  :   str(job_id),
                # custom_id COMES BACK ON THE CAPTURE WEBHOOK, IT IS HOW A LATE
                # DENIAL IS MATCHED BACK TO THIS JOB
                "custom_id"     :   str(job_id),
                "amount": {
                    "currency_code" :   JOB_CURRENCY,
                    "value"         :   JOB_AMOUNT
                }
            }
        ],
        "payment_source": {
            "venmo": {
                "vault_id"  :   vault['paypal_valut_id']
            }
        }
    }

    payload_data =  {
        "paypal_req_id" :   paypal_req_id,
        "payload"       :   payload,
        "access_token"  :   access_token,
        "url"           :   paypal_url('/v2/checkout/orders'),
        "job_id"        :   job_id,
        "user_id"       :   login_user,
        "source_type"   :   "venmo"
    }

    '''THE ORDER CALL, FAILURE LOGGING AND JOB UPDATE ARE SHARED WITH THE CARD FLOW'''
    from openup.background_paypal import PaypalPayment
    PaypalPayment.background_payments(payload_data)

    return True
