# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse

# Import token verifications
from openup_api.views.auth_views import token_verification
 
# import datetime
from datetime import datetime

# Import Models here
from openup_app.models import Payment,Registration,Jobs,PaypalInfo

# Import Serializer
from openup_app.serializers import PaymentSerializer,RegisterSerializer,JobsSerializer

# Import validation
from .validation import check_text,verify_card

# import stripe
import stripe
from openup.create_cust import stripeCustomer

# import Payments class 
from openup.payment import Payments

from openup.background_paypal import PaypalPayment


from openup.fcm import FCM


# IMPORT SHARED TASK
from celery import shared_task


# Import Queryset
from django.db.models import Q

import environ
env = environ.Env()
environ.Env.read_env()

# Api for add and edit card data
import requests




# SET CLIENT ID AND SECRET IN .ENV FILE

client_id=env("CLIENT_ID")
client_secret=env("CLIENT_SECRET")


# tehatol844@iturchia.com

@api_view(['POST'])
def add_card(request):
     #  Token Verification

    token           =       request.headers['Authorization']
    user_token      =       token.replace("Bearer",'')
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })
    
    # if token verified
    else:
        # required data
        payment_id          =   request.data.get('payment_id',None)
        # if payment not provided new payment data added
        if payment_id == None:

            # required data
            card_no             =   request.data.get('card_no',None)
            card_cvv            =   request.data.get('card_cvv',None)
            card_holder_name    =   request.data.get('cust_name',None)
            card_validity       =   request.data.get('card_validity',None)
            card_type           =   request.data.get('card_type',None)
            # check card_no provided or not
            if card_no is None or card_no == "":
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Please provide card number ",
                        })
            flag = verify_card(card_no)
            if flag == False:
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Please provide valid card number ",
                        })
            # validates card number     
            # check cvv provided or not
            if  card_cvv is None or card_cvv == "":
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Please provide cvv card number ",
                        })
            # Validates cvv contains numbers only
            # check for card holder name 
            if card_holder_name is None or card_holder_name ==  "":
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Please provide card holder name ",
                        })

            # validates card holder name 
            check_name = check_text(card_holder_name)
            if check_name == False:
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Name should be in string",
                        })

            # check for card_validity 
            if card_validity is None or card_validity =="":
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Please provide card validity date",
                        })
            # check for card_type 

            if card_type is None or card_type =="":
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Please provide card validity date",
                        })
            
            # current datestamp
            created_at  =     datetime.now()
            # formats datetime stamp
            validity    =   (datetime.strptime(card_validity,"%m/%y")).strftime("%Y-%m-%d")

            # change current date to unix date
            date_today  =           datetime.now()
            dt          =           datetime.strftime(date_today,"%m/%y")
            time        =           (datetime.strptime(dt,"%m/%y"))
            date_unix   =           datetime.timestamp(time)*1000

            # change validity date to timestamp 
            v               =       (datetime.strptime(card_validity,"%m/%y"))
            validity_unix   =       datetime.timestamp(v)*1000
            if validity_unix    <   date_unix:
                  return JsonResponse({
                                "success"     :   0,
                                "message"     :   "card validity expired",
                        })

            user_id     =   check_user['session_user']
            user_record =   Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
            # card data to be added
            card_data = {
            "user_card_no"      :   card_no,
            "card_cvv"          :   card_cvv,
            "card_name"         :   card_holder_name,
            "card_validity"     :   validity,
            "card_type"         :   card_type,
            "created_at"        :   created_at,
            "user"              :   user_record.user_id
            
            }
            # serializer instance
            card_ser = PaymentSerializer(data=card_data)

            if card_ser.is_valid():
                card_ser.save()
                return JsonResponse({
                                "success"     :   1,
                                "message"     :   "Card details added",
                        })
            else:
                 return JsonResponse({
                                    "success"     :   0,
                                    "message"     :   "some error occured",
                                    "error"       :     card_ser.errors
                            })
            
        # if payment  provided edit payment data

        else:
            # data to be edit
            card_no             =   request.data.get('card_no',None)
            card_cvv            =   request.data.get('card_cvv',None)
            card_holder_name    =   request.data.get('cust_name',None)
            card_validity       =   request.data.get('card_validity',None)
            card_type           =   request.data.get('card_type',None)
            validity            =   (datetime.strptime(card_validity,"%m/%y")).strftime("%Y-%m-%d")

            # change current date to unix date
            date_today  =           datetime.now()
            dt          =           datetime.strftime(date_today,"%m/%y")
            time        =           (datetime.strptime(dt,"%m/%y"))
            date_unix   =           datetime.timestamp(time)*1000

            # change validity date to timestamp 
            v               =       (datetime.strptime(card_validity,"%m/%y"))
            validity_unix   =       datetime.timestamp(v)*1000
            if validity_unix    <   date_unix:
                  return JsonResponse({
                                "success"     :   0,
                                "message"     :   "card validity expired",
                        })


            # creates empty dict
            update_data = { }

            if card_no is not None:
                update_data["user_card_no"] =  card_no

            if card_cvv is not None:
                update_data["card_cvv"] =  card_cvv

            if card_holder_name is not None:
                update_data["card_name"] =  card_holder_name

            if card_validity is not None:
                update_data["card_validity"] =  validity

            if card_type is not None:
                update_data["card_type"] =  card_type


            user_id     =   check_user['session_user']
            user_record =   Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
            update_data["user"] = user_record.user_id
            
            # get payment record instance
            payment_rec     =       Payment.objects.exclude(is_delete=1).get(payment_id=payment_id)

            # serializer instance 
            payment_serializer = PaymentSerializer(instance=payment_rec,data=update_data,partial=True)
        
            if payment_serializer.is_valid():
                payment_serializer.save()
                return JsonResponse({
                                    "success"     :   1,
                                    "message"     :   "Card details Updated",
                            })
            else:
                return JsonResponse({
                                    "success"     :   0,
                                    "message"     :   "some error occured",
                                    "error"       :     payment_serializer.errors
                            })
            


        
# Api for card details

@api_view(['POST'])
def card_details(request):

    # token verification
    token           =       request.headers['Authorization']
    user_token      =       token.replace("Bearer",'')
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })
    else:

        # required data
        payment_id  =   request.data.get('payment_id',None)
        # check if payment_id provided or not
        if payment_id == None or payment_id ==" ":

            return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide payment id",
        })
        try:
            # Get payment details
            payment_record  =   Payment.objects.exclude(is_delete=1).get(payment_id=payment_id)
        
        except:
            payment_record = None
        
        if payment_record == None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "please provide valid payment id",
        })

        payment_ser     =   PaymentSerializer(payment_record).data

        # Remove data from serializer
        payment_ser.pop('created_at')
        payment_ser.pop('update_at')
        payment_ser.pop('is_delete')

        # format datetime 
        validity = (datetime.strptime(payment_ser['card_validity'],"%Y-%m-%dT%H:%M:%SZ")).strftime("%Y-%m-%d")        
        payment_ser['card_validity'] = validity        
        
        card_data = {
        "card_data" :   payment_ser
        }
                
        return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Card Details",
                    "data"        :   card_data

            })


 
       

stripe.api_key = env('STRIPE_API')
 
@api_view(['POST'])
def create_customer(request,*args,**kwargs):

    token           =       request.headers['Authorization']
    user_token      =       token.replace("Bearer",'')
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
            })
    else:
        user_id         =       check_user['session_user']
        user_details    =       Registration.objects.exclude(user_is_delete = 1).get(user_id=user_id)
        
        try:
            card_id     =       Payment.objects.exclude(is_delete=1).filter(user_id=user_id).values('payment_id').first()['payment_id']
        except:
            card_id     =       None


        # CUSTOMER ID IS STORED IN USER LOGIN WHILE USER REGISTRATION
        try:
            cust_id         =   user_details.user_stripe_id
        except:
            cust_id         =   None


        # code to create ephemeral key to stripe 
        ephemeralKey    = stripe.EphemeralKey.create(
                            customer=cust_id,
                            stripe_version='2022-11-15',)

        # setup intent
        setupIntent  = stripe.SetupIntent.create(customer=cust_id,payment_method_types=["card"])  
        
        '''code for payment intent'''

        data = {
        "response_data" :   cust_id,
        "customer_id"   :   cust_id,
        "setup_intent"  :   setupIntent.client_secret,
        "ephemeralKey"  :   ephemeralKey,
        }

        return JsonResponse({
            "success"    :   1,
            "message"   :   "payment method added successfully",
            "data"      :   data
        })

         
        














@api_view(['POST'])
def link_payment_method(request):
    token           =       request.headers['Authorization']
    user_token      =       token.replace("Bearer",'')
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
            })
    else:
        cus_id          =       request.data.get('cust_id')
        user_id         =       check_user['session_user']
         
 
        try:
            user_rec     =       Registration.objects.exclude(user_is_delete=1).get(user_id=int(user_id))
        except:
            user_rec     =       None

        response_data = stripe.PaymentMethod.list(
            customer=cus_id,
            type="card",
        ) 


        update_data = {
                "user_payment_id" : response_data["data"][0]['id'], 
        }
        user_ser        =   RegisterSerializer(instance=user_rec,data=update_data,partial=True)
        
        if user_ser.is_valid():

            user_ser.save()
            # code for payment intent
             
            return JsonResponse({
                        "success"    :    1,
                        "message"   :   "payment method added successfully",
                     })   
        else:
          
            return JsonResponse({
                        "success"    :    0,
                        "message"   :   "error occured",
                     })

        
 


'''function to check customer created of not'''

def check_stripe(user_id):

    try:
        user_record     =       Registration.objects.exclude(user_is_delete=1).get(user_id=int(user_id))
    except:
        user_record     =   None

    if user_record.user_role == 1 or user_record.user_stripe_id != None:
        return False
    
    response_data   =  stripe.Customer.create(description="client added to stripe",
                                       email = user_record.user_email,
                                       name  = user_record.user_first_name+user_record.user_last_name)

    cust_id         = response_data['id']
    # code to create ephemeral key to stripe
    update_data = {
                "user_stripe_id" : cust_id, 
               }    

    
    user_serializer = RegisterSerializer(instance=user_record,data=update_data,partial=True)
    if user_serializer.is_valid():
        user_serializer.save()
        return True







'''if payment failed in stripe then ask for payment api called by employee'''


@api_view(['POST'])
def ask_for_payment(request):
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })
    else:
        emp  =   check_user['session_user']
        job  =   request.data.get('job_id')
        if job == None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "please provide job id",
        })
        
        job_id  =  Jobs.objects.exclude(Q(is_delete=1) and Q(job_status_id=4)).get(job_id=int(job))

        if emp != job_id.user.user_id:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "unauthorized access",
        })

        if job_id.job_pay_status == 0 and (job_id.job_payment_id == "" or job_id.job_payment_id == None):
    
            user_id     =       job_id.user.user_id
            user_record =       Registration.objects.exclude(user_is_delete=1).get(user_id= user_id)
            data = { 
             'title'                      :   'request for payment',             
             'notificationScreenType'     :   'payment_request',
             'message'                    :   'Please make payment asap',
             'job_id'                     :   str(job_id.job_id),  
            }             
            noti_data   =   {
                    "fcm_token"     :   user_record.user_fcm_token,
                    "device"        :   user_record.device_type,
            }                    
            noti_data['data']       =   data
            send_notification.delay(noti_data)
            return JsonResponse({
            "success"   :       1,
            "message"   :   "payment notification sent and payment is pending" 
            })
        
        else:

            return JsonResponse({
            "success"   :       0,
            "message"   :   "job payment is done" 
            })

            
     
@shared_task()        
def send_notification(noti_data):  
    FCM.send_notification(noti_data)


 



 
@api_view(['POST'])
def manual_payment(request,*args,**kwargs):

    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
            })
    else:
        user_id         =       check_user['session_user']
 
        user_details    =       Registration.objects.exclude(user_is_delete = 1).get(user_id=user_id)
   
        # CUSTOMER ID IS STORED IN USER LOGIN WHILE USER REGISTRATION
        try:
            cust_id         =   user_details.user_stripe_id
        except:
            cust_id         =   None

        # code to create ephemeral key to stripe 
        ephemeralKey    = stripe.EphemeralKey.create(
                            customer=cust_id,
                            stripe_version='2022-11-15',)

        # setup intent
        setupIntent  = stripe.PaymentIntent.create(
            customer            =   cust_id,
            amount              =   500*100,
            currency            =   'inr',
            payment_method_types=   ["card"])  


      
        '''code for payment intent'''

        data = {
        "response_data" :   cust_id,
        "customer_id"   :   cust_id,
        "setup_intent"  :   setupIntent.client_secret,
        "ephemeralKey"  :   ephemeralKey,
        "payment_id"    :   setupIntent.id
        }
      
        return JsonResponse({
            "success"    :   1,
            "message"   :   "payment added successfully",
            "data"      :   data
        })



 




# WOKING CODE OF LIVE
#  This API will Call for manual payments through job list


@api_view(['POST'])
def manual_payment_success(request):

    token           =       request.headers['Authorization']
    user_token      =       token.replace("Bearer",'')
    check_user      =       token_verification(user_token)
    job_id          =       request.data.get('job_id')
    payment_id      =       request.data.get('payment_id')

    
    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
            })
    else:
        user_id         =   check_user['session_user']
        payment_type    =   request.data.get('payment_type')
        job_id          =   request.data.get('job_id')
        paypal_req_id   =   request.data.get("paypal_req_id")

        job_record =  Jobs.objects.exclude(is_delete=1).get(job_id=int(job_id))
        user_record = Registration.objects.exclude(user_is_delete=1).get(user_id=job_record.user.user_id)
        

        if payment_type == "stripe":
                 
                # '''Payment code '''
                background_payment.delay(user_id,job_id)
    
        if payment_type=="paypal":

            # try: 
            #     check_job = Jobs.objects.exclude(is_delete=1).filter(user=user_rec.user_id).exists()
            # except:
            #     check_job = False
            # # # if no job found means user is new
            # if check_job == False:

                data = {
                    "user"          :   user_id,
                    "job_id"        :   job_id,
                    "paypal_req_id" :   paypal_req_id,
                    
                }
                    
                paypal_payment.delay(data)



        # update_date = {
        #     "job_pay_status"     :      1,
        #     "job_payment_id"     :      payment_id
        # }  

        # response_data = stripe.PaymentMethod.list(
        #     customer=user_record.user_stripe_id,
        #     type="card",
        # ) 
        # data = {
        #         "user_payment_id" : response_data["data"][0]['id'], 
        # }

        # '''code for payment intent'''
        # job_serializer  =   JobsSerializer(instance=job_record,data=update_date,partial=True)
        # user_ser        =   RegisterSerializer(instance=user_record,data=data,partial=True)
        # if job_serializer.is_valid():
        #     job_serializer.save()

        # if user_ser.is_valid():
        #     user_ser.save()  
        return JsonResponse({
            "success"    :   1,
            "message"   :   "payment added successfully",
        })
    





'''
code for background process
if its first payment then payment will not occured STRIPE PAYMENT
'''
@shared_task()
def background_payment(user_id,job_id):
    
    try:
        payment_id  =   Payment.objects.filter(user=int(user_id)).values("payment_id").first()["payment_id"]  
    except:
        pass

    try:
        payment     =   Payment.objects.get(payment_id=payment_id)
    
    except:
        pass
   
    try:
        user = Registration.objects.exclude(user_is_delete=1).get(user_id=int(user_id))

    except:
        pass
    
    data = {
        "amount"            :     500*100,
        "currency"          :    "inr",
        "customer"          :     user.user_stripe_id,
        "payment_method_id" :     user.user_payment_id,
        "job_id"            :     job_id,
        "user_id"           :     user_id,
         "metadata"         :      {   
        "name"              :   user.user_first_name+' '+user.user_last_name
          }
        }
   
    '''background payment method in payment.py'''
 
    Payments.background_payments(data)
    return True






# RECURRING PAYPAL PAYMENT

@shared_task()
def paypal_payment(data):
        

        job_id           =   data['job_id']
        paypal_req_id   =   data['paypal_req_id']  # random text 
        login_user      =   data['user']
        paypal_data     =   PaypalInfo.objects.filter(paypal_user=login_user).values().first()
        user            =   Registration.objects.get(user_id=login_user)
        # get access token
        url             =   'https://api-m.sandbox.paypal.com/v1/oauth2/token'
        headers         =   {'Accept': 'application/json', 'Accept-Language': 'en_US', 'PayPal-Request-Id': paypal_req_id,}
        data            =   {'grant_type': 'client_credentials'}
        auth            =   (client_id, client_secret)
        response        =   requests.post(url, headers=headers, data=data, auth=auth)
        access_token    =   response.json()['access_token']
 
        # # Create payment payload
        # payload = {
        #     "intent": "CAPTURE",
        #     "payer": {
        #         "payment_method": "paypal",
        #         "payer_info": {
        #             "customer_id": paypal_data['paypal_cust_id']
        #         }
        #     },
        #      "purchase_units": [
        #     {
        #     "reference_id": "111",    #Change id on each request
        #     "amount": {
        #         "currency_code": "USD",
        #         "value": "110.00"
        #     }
        #     }
        # ],
        #     "payee": {
        #         "merchant_id": paypal_data['paypal_valut_id'] 
        #     }
        # }

        # FUTURE PAYMENTS WILL BE CREATED BY USING VALUT ID 

        payload={
            "intent": "CAPTURE",
          
            "purchase_units": [
                {
                     "reference_id": "1123",
                    "amount": {
                        "currency_code": "USD",
                        "value": "100.00"
                    },
           
                }
            ],
            "payment_source": {
                "card": {
                    "vault_id":paypal_data['paypal_valut_id'] 
                            }          
                        }
                    }

        # # Send payment request
        # url = 'https://api-m.sandbox.paypal.com/v2/checkout/orders'
        # headers = {'Content-Type': 'application/json','PayPal-Request-Id': paypal_req_id, 'Authorization': 'Bearer ' +access_token}
        # response = requests.post(url, headers=headers, json=payload)
        # response_data = json.loads(response.text)

        # try:
        #     error = response_data["name"]
        # except:
        #     error = False

        # if error == "UNPROCESSABLE_ENTITY" or error == "INVALID_REQUEST":
        #     paypal_data = PaymentFailedInfo(
        #         user_id=user.user_id, job_id=job_id, payment_fail_response=response_data, created_at=timezone.now()
        #     )
        #     paypal_data.save()
        #     return True

        # try:
        #     status = response_data["status"]
        
        # except:
        #     status = False
        
        # if status == "PAYER_ACTION_REQUIRED":
        #     paypal_data = PaymentFailedInfo(
        #         user_id=user.user_id, job_id=job_id, payment_fail_response=response_data, created_at=timezone.now()
        #     )
        #     paypal_data.save()
        #     return True
        

        
        payload_data = {
            "paypal_req_id" :   paypal_req_id,
            "payload"       :   payload,
            "access_token"  :   access_token,
            "url"           :   url,
            "job_id"        :   job_id,
            "user_id"       :   user.user_id,
            "paypal_valut_id":paypal_data['paypal_valut_id']
            }
        # SEND PAYLOAD TO BACKGROUND TO INITIATE PAYMENT

        PaypalPayment.background_payments(payload_data)


        # Working foreground flow
        # data = {
        #     "job_id" : job_id,
        # }
        # # # Update job after successfull payment.
        # job_record = Jobs.objects.exclude(is_delete=1).get(job_id=int(data['job_id']))   

        
        # update_payment_status = {
        #         "job_payment_id"    :      data['job_id'],
        #         "job_pay_status"    :      1,
                 
        #         } 
        
        # job_ser  = JobsSerializer(instance=job_record,data=update_payment_status,partial=True)
        # if job_ser.is_valid():
        #     job_ser.save()

        # pay_info = SuccessPayments(
        #     pay_user = login_user,
        #     pay_job = job_id,
        #     pay_type = "paypal",
        #     pay_response = response_data,
        #     create_at = timezone.now()
        # )
        # pay_info.save()
        return True