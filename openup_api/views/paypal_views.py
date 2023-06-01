# Create your views here.
from rest_framework.decorators import api_view

import requests

# import Json Response
from django.http.response import JsonResponse

# Import token verifications
from openup_api.views.auth_views import token_verification
import datetime

@api_view(['POST'])
def paypal(request):
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')  
    check_user      =       token_verification(user_token)
    
    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })
    
    # if token verified
    else:
        headers = {
            'Authorization': 'Bearer A21AAGHr9qtiRRXH4oYcQokQgV99rGqEIfgrr8xHCclP0OzmD9KVgg5ppIIg1jzJgQkV4wd02svIvBJyg6cLFJjFow_SjBhxQ',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'PayPal-Request-Id': 'SUBSCRIPTION-21092019-001',
            'Prefer': 'return=representation',
        }

        data = { "plan_id": "P-5ML4271244454362WXNWU5NQ", 
                "start_time": datetime.datetime.now(),
                "quantity": "20", 
                "shipping_amount": { "currency_code": "USD", "value": "10.00" }, 
                "subscriber": { "name": { "given_name": "John", "surname": "Doe" }, 
                                "email_address": "customer@example.com", 
                                "shipping_address": { "name": { "full_name": "John Doe" }, 
                                                    "address": { "address_line_1": "2211 N First Street", 
                                                                "address_line_2": "Building 17", 
                                                                "admin_area_2": "San Jose", 
                                                                "admin_area_1": "CA", 
                                                                "postal_code": "95131", 
                                                                "country_code": "US" } } }, 
                                                                "application_context": { "brand_name": "walmart", "locale": "en-US", 
                                                                                        "shipping_preference": "SET_PROVIDED_ADDRESS", 
                                                                                        "user_action": "SUBSCRIBE_NOW", 
                                                                                        "payment_method": { "payer_selected": "PAYPAL", 
                                                                                                            "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED" }, 
                                                                                                            "return_url": "https://example.com/returnUrl", 
                                                                                                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                    
                                                                                                            "cancel_url": "https://example.com/cancelUrl" } }

        response = requests.post('https://api-m.sandbox.paypal.com/v1/billing/subscriptions', headers=headers, data=data)

        print(response)
        return JsonResponse({
                "success"       :   0,
                "message"       :   "cust created",
                "data"              :   response
       })