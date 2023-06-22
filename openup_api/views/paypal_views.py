# Create your views here.
from rest_framework.decorators import api_view


# import Json Response
from django.http.response import JsonResponse

# Import token verifications
from openup_api.views.auth_views import token_verification
import datetime
import requests
import json
from django.http import HttpRequest
#  Import Serializer
from openup_app.serializers import RegisterSerializer
from openup_app.models import Registration, PaypalInfo, WebhookData
 


client_id       =   'AT2Eg75NhoHdw91flmYm33N-1dQZNqhdupHFgRK6ZeXaiVVsazGzAYOandAn4w8eaB51oI4O6foq3pUN'
client_secret   =   'EN_1SJC4D-gaenjo71ZeVtqtjojE6b2FyQqpLl4Sali-qENSPF0ybY5ixhYdzpEbl23qoLxXJZ2r3C09'
     
 
# yahiwo2214@bodeem.com 


# CREATE FIRST PAYMENT IN PAYPAL AND SAVE VALUT ID FOR LATER USE

@api_view(['POST'])
def create_customer(request):
    token = request.headers.get('Authorization')
    user_token = token.replace("Bearer", "").strip()  # Remove leading/trailing spaces
    
    check_user = token_verification(user_token)
    
    if check_user is None:
        return JsonResponse({
            "success": 0,
            "message": "Unauthorized User",
        })
    else:
        
        url             =   'https://api-m.sandbox.paypal.com/v1/oauth2/token'
        headers         =   {'Accept': 'application/json', 'Accept-Language': 'en_US'}
        data            =   {'grant_type': 'client_credentials'}
        auth            =   (client_id, client_secret)
        response        =   requests.post(url, headers=headers, data=data, auth=auth)
        access_token    =   response.json()['access_token']

        card_no          =  request.data.get('card_no')
        expiry           =  request.data.get('expiry')
        card_holder_name =  request.data.get('card_holder_name')
        address_line_1   =  request.data.get('address_line_1')
        address_line_2   =  request.data.get('address_line_2')
        admin_area_2     =  request.data.get('admin_area_2')  
        admin_area_1     =  request.data.get('admin_area_1')
        postal_code      =  request.data.get('postal_code')
        country_code     =  request.data.get('country_code')
        paypal_req_id    =  request.data.get('paypal_req_id') # random text 
        # access_token     =  request.data.get('access_token')

        
        login_customer = check_user['session_user']
        user = Registration.objects.get(user_id=login_customer)

        #  payapl authentication
        headers = {
            'Content-Type': 'application/json',
            'PayPal-Request-Id': paypal_req_id,  # change id on each request
            'Authorization': 'Bearer '+ access_token,
        }

        # Working static data 
        # data = {
        # "intent": "CAPTURE",
        # "payment_source": {
        #         "card": {
        #             "number": "5555555555554444",
        #             "expiry": "2024-04",
        #             "name": "swap pathak",
        #             "billing_address": {
        #                 "address_line_1": "2211 N First Street",
        #                 "address_line_2": "Building 17",
        #                 "admin_area_2": "San Jose",
        #                 "admin_area_1": "CA",
        #                 "postal_code": "95131",
        #                 "country_code": "US"
        #             },
        #             "attributes": {
        #                 "vault": {
        #                     "store_in_vault": "ON_SUCCESS"
        #                 }
        #             }
        #         }
        #     },
        # "purchase_units": [
        #     {
        #     "reference_id": "1234",    #Change id on each request
        #     "amount": {
        #         "currency_code": "USD",
        #         "value": "110.00"
        #     }
        #     }
        # ]
        # }
        data = {
        "intent": "CAPTURE",
        "payment_source": {
                "card": {
                    "number": card_no,
                    "expiry": expiry,
                    "name"  : card_holder_name,
                    "billing_address": {
                        "address_line_1": address_line_1,
                        "address_line_2": address_line_2,
                        "admin_area_2"  : admin_area_2,
                        "admin_area_1"  : admin_area_1,
                        "postal_code"   : postal_code,
                        "country_code"  : country_code
                    },
                    "attributes": {
                        "vault": {
                            "store_in_vault": "ON_SUCCESS"
                        }
                    }
                }
            },
        "purchase_units": [
            {
            "reference_id": "111",    #Change id on each request
            "amount": {
                "currency_code": "USD",
                "value": "110.00"
            }
            }
        ]
        }


        #  payapl order api call to save valut id
        response = requests.post('https://api-m.sandbox.paypal.com/v2/checkout/orders', headers=headers, json=data)
        
        resp_data = json.loads(response.text)
         
        if resp_data["status"] == "COMPLETED":
             
            valut_id = resp_data['payment_source']["card"]["attributes"]["vault"]["id"]

            cust_id  = resp_data['payment_source']["card"]["attributes"]["vault"]["customer"]["id"]

            paypal_data = PaypalInfo(
                        paypal_user     =   user,
                        paypal_valut_id =   valut_id,
                        paypal_cust_id  =   cust_id,
                        is_delete       =   0,
                        created_at      =   datetime.datetime.now()   
            )
            paypal_data.save()

            return JsonResponse({
                        "success"       :   1,
                        "message"       :   "payment success",
                        "data"          :   resp_data

                })             
        else:
             
            return JsonResponse({
                    "success"       :   0,
                    "message"       :   "Something went wrong",
                     
            })
             



# Code for future payments


@api_view(['POST'])

def paypal_payment(request):

    token = request.headers.get('Authorization')
    user_token = token.replace("Bearer", "").strip()  # Remove leading/trailing spaces
    
    check_user = token_verification(user_token)
    
    if check_user is None:
        return JsonResponse({
            "success": 0,
            "message": "Unauthorized User",
        })
    else:
        paypal_req_id   =   request.data.get('paypal_req_id')  # random text 
        
        login_user      =   check_user['session_user']
        paypal_data     =   PaypalInfo.objects.filter(paypal_user=login_user).values().first()
        
        # get access token
        url             =   'https://api-m.sandbox.paypal.com/v1/oauth2/token'
        headers         =   {'Accept': 'application/json', 'Accept-Language': 'en_US', 'PayPal-Request-Id': paypal_req_id,}
        data            =   {'grant_type': 'client_credentials'}
        auth            =   (client_id, client_secret)
        response        =   requests.post(url, headers=headers, data=data, auth=auth)
        access_token    =   response.json()['access_token']
 
        # # Create payment payload
        payload = {
            "intent": "CAPTURE",
            "payer": {
                "payment_method": "paypal",
                "payer_info": {
                    "customer_id": paypal_data['paypal_cust_id']
                }
            },
             "purchase_units": [
            {
            "reference_id": "111",    #Change id on each request
            "amount": {
                "currency_code": "USD",
                "value": "110.00"
            }
            }
        ],
            "payee": {
                "merchant_id": paypal_data['paypal_valut_id'] 
            }
        }

        # Send payment request
        url = 'https://api-m.sandbox.paypal.com/v2/checkout/orders'
        headers = {'Content-Type': 'application/json','PayPal-Request-Id': paypal_req_id, 'Authorization': 'Bearer ' +access_token}
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        # print(response_data)
        
        return JsonResponse({
                        "success"       :   1,
                        "message"       :   "payment success",
                        "data"          :   response_data
                })   




# THIS API WILL CREATE WEBHOOK 
@api_view(['POST'])

def create_webhook(request: HttpRequest):
    # random text 
    paypal_req_id   =   request.data.get('paypal_req_id') 
    url             =   'https://api-m.sandbox.paypal.com/v1/oauth2/token'
    headers         =   {'Accept': 'application/json', 'Accept-Language': 'en_US', 'PayPal-Request-Id': paypal_req_id,}
    data            =   {'grant_type': 'client_credentials'}
    auth            =   (client_id, client_secret)
    response        =   requests.post(url, headers=headers, data=data, auth=auth)
    access_token    =   response.json()['access_token']


    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer '+access_token,
    }

    current_url = request.build_absolute_uri()
 
    data = { "url": current_url, "event_types": 
            [ 
                { 
                    "name": "PAYMENT.AUTHORIZATION.CREATED" 
                }, 
                { 
                    "name": "PAYMENT.AUTHORIZATION.VOIDED" 
                } 
            ] 
    }
    response = requests.post('https://api-m.sandbox.paypal.com/v1/notifications/webhooks', headers=headers, json=data)

    resp_data = json.loads(response.text)

    if resp_data['name']:
        return JsonResponse({
                        "success"       :   0,
                        "message"       :   "something went wrong",

                })

    else:
        return JsonResponse({
                            "success"       :   1,
                            "message"       :   "webhook created",
                            "data"          :   response.text
                    })  
    
    




# PAYPAL WILL CALL THIS API AND SAVE TOKEN IN DATABASE

@api_view(['POST'])

def paypal_payment_token_receiver(request):

        token_info = request.data.get('token_receiver_info')    

        data = json.loads(token_info)

        webhook_data    =   WebhookData(
            webhook_data   =   data,
            is_delete       =   0,
            created_at      =   datetime.datetime.now()
        )

        webhook_data.save()

        return JsonResponse({
                            "success"       :   1,
                            "message"       :   "Token generated ",
                    })  








 














# def get_access_token(client_id,client_secret):
#     token_endpoint = "https://api.sandbox.paypal.com/v1/oauth2/token"


 
#     # Set the request parameters to obtain the access token
#     token_data = {
#         "grant_type": "client_credentials"
#     }

#     # Set the request headers
#     headers = {
#         "Accept": "application/json",
#         "Accept-Language": "en_US"
#     }

#     # Set the authentication credentials
#     auth = (client_id, client_secret)

#     # Make the request to obtain the access token
#     response = requests.post(token_endpoint, data=token_data, headers=headers, auth=auth)
     
#     # Check if the request was successful
#     if response.status_code == 200:
#         access_token = response.json()["access_token"]
#         token_type = response.json()["token_type"]
#         print("Access token:", access_token)
#         print("Token type:", token_type)
#         return access_token
#     else:
#         print("Failed to obtain access token. Error:", response.text)














@api_view(['POST'])
    # Save the customer ID for later use
def save_customer_id(customer_id):
        # You can implement your own logic to save the customer ID, such as storing it in a database or file
        # For demonstration purposes, we'll simply print it here
        print(f'Saving customer ID: {customer_id}')

        # Usage
        customer_id = create_customer()


        if customer_id:
            save_customer_id(customer_id)

