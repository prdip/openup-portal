'''
SHARED PAYPAL HELPERS.

THE API HOST USED TO BE HARDCODED AS THE SANDBOX HOST IN EVERY SINGLE CALL SITE.
IT NOW COMES FROM PAYPAL_BASE_URL IN .env AND STILL DEFAULTS TO THE SANDBOX HOST,
SO NOTHING CHANGES UNTIL THE LIVE HOST IS SET:

    PAYPAL_BASE_URL=https://api-m.paypal.com

VENMO ONLY WORKS ON A LIVE ACCOUNT THAT PAYPAL HAS ENABLED IT FOR, SO THIS HAS TO
BE SWITCHABLE WITHOUT EDITING SOURCE.
'''

import requests

import environ
env = environ.Env()
environ.Env.read_env()


PAYPAL_BASE_URL     =   env('PAYPAL_BASE_URL', default='https://api-m.sandbox.paypal.com').rstrip('/')

client_id           =   env('CLIENT_ID')
client_secret       =   env('CLIENT_SECRET')


'''BUILDS A FULL PAYPAL URL FROM A PATH LIKE "/v2/checkout/orders"'''
def paypal_url(path):
    if not path.startswith('/'):
        path = '/' + path
    return PAYPAL_BASE_URL + path


'''
OAUTH ACCESS TOKEN. RETURNS None INSTEAD OF RAISING WHEN PAYPAL REJECTS THE
CREDENTIALS, SO CALLERS CAN RETURN A REAL ERROR MESSAGE TO THE APP.
'''
def get_access_token(paypal_req_id=None):

    headers =   {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    if paypal_req_id:
        headers['PayPal-Request-Id'] = paypal_req_id

    try:
        response    =   requests.post(
                            paypal_url('/v1/oauth2/token'),
                            headers=headers,
                            data={'grant_type': 'client_credentials'},
                            auth=(client_id, client_secret),
                            timeout=30,
                        )
        return response.json()['access_token']
    except Exception:
        return None


'''
NEWEST VAULT RECORD FOR A USER, AS A DICT (SAME SHAPE THE CALL SITES ALREADY USE).

BEFORE VENMO EVERY CALLER DID .filter(paypal_user=user).values().first(), WHICH IS
WHATEVER ROW THE DB HANDED BACK FIRST. THAT IS THE WRONG SOURCE AS SOON AS A USER
HAS BOTH A CARD AND A VENMO ACCOUNT VAULTED, SO THE SOURCE TYPE IS NOW PART OF THE
LOOKUP. RETURNS None WHEN THE USER HAS NOTHING VAULTED.
'''
def get_vault_record(user_id, source_type=None):

    from openup_app.models import PaypalInfo

    records =   PaypalInfo.objects.exclude(is_delete=1).filter(paypal_user=user_id)

    if source_type:
        typed = records.filter(paypal_source_type=source_type).order_by('-paypal_info_id').values().first()
        if typed:
            return typed
        '''
        LEGACY ROWS WRITTEN BEFORE paypal_source_type EXISTED ARE ALL CARDS, AND THE
        MIGRATION DEFAULTS THEM TO 'card'. FOR ANY OTHER SOURCE A MISSING ROW MEANS
        THE USER SIMPLY HAS NOT VAULTED IT, SO DO NOT FALL BACK TO A DIFFERENT SOURCE.
        '''
        if source_type != 'card':
            return None

    return records.order_by('-paypal_info_id').values().first()


'''
VERIFIES THAT A WEBHOOK REALLY CAME FROM PAYPAL.

WITHOUT THIS, ANYONE WHO KNOWS THE WEBHOOK URL COULD POST A "CAPTURE COMPLETED"
EVENT AND GET A JOB MARKED AS PAID. RETURNS:

    True    -> PAYPAL CONFIRMED THE SIGNATURE, SAFE TO ACT ON
    False   -> BAD SIGNATURE, IGNORE THE EVENT
    None    -> PAYPAL_WEBHOOK_ID IS NOT CONFIGURED, SO NOTHING CAN BE VERIFIED
'''
def verify_webhook(headers, event_body):

    webhook_id  =   env('PAYPAL_WEBHOOK_ID', default='')
    if webhook_id == '':
        return None

    access_token    =   get_access_token()
    if access_token is None:
        return False

    payload =   {
        "auth_algo"         :   headers.get('HTTP_PAYPAL_AUTH_ALGO', ''),
        "cert_url"          :   headers.get('HTTP_PAYPAL_CERT_URL', ''),
        "transmission_id"   :   headers.get('HTTP_PAYPAL_TRANSMISSION_ID', ''),
        "transmission_sig"  :   headers.get('HTTP_PAYPAL_TRANSMISSION_SIG', ''),
        "transmission_time" :   headers.get('HTTP_PAYPAL_TRANSMISSION_TIME', ''),
        "webhook_id"        :   webhook_id,
        "webhook_event"     :   event_body,
    }

    try:
        response    =   requests.post(
                            paypal_url('/v1/notifications/verify-webhook-signature'),
                            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + access_token},
                            json=payload,
                            timeout=30,
                        )
        return response.json().get('verification_status') == 'SUCCESS'
    except Exception:
        return False


'''
PULLS THE LINK THE BUYER HAS TO OPEN TO APPROVE A VENMO PAYMENT OUT OF A PAYPAL
RESPONSE. PAYPAL CALLS IT "payer-action" FOR ORDERS AND SETUP TOKENS, BUT OLDER
RESPONSES USE "approve", SO BOTH ARE ACCEPTED.
'''
def approval_link(resp_data):
    for link in (resp_data.get('links') or []):
        if link.get('rel') in ('payer-action', 'approve'):
            return link.get('href')
    return None
