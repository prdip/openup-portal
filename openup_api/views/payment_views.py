# Create your views here.
from rest_framework.decorators import api_view

from django.shortcuts import render,redirect


# import Json Response
from django.http.response import JsonResponse

# Import token verifications
from openup_api.views.auth_views import token_verification

import datetime

from datetime import datetime

# Import Models here
from openup_app.models import Payment,Registration

# Import Serializer
from openup_app.serializers import PaymentSerializer

# Import validation
from .validation import check_text,verify_card

from django.conf import settings





# Api for add and edit card data

@api_view(['POST'])
def add_card(request):
     #  Token Verification

    user_token      =       request.data.get('user_token',None)
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
    user_token      =       request.data.get('user_token',None)
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



       
# Api for card details

@api_view(['POST'])
def card_delete(request):

     # token verification
    user_token      =       request.data.get('user_token',None)
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
        if payment_id == None or payment_id =="":

            return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide payment id",
        })

         # Get payment details
        payment_record  =   Payment.objects.exclude(is_delete=1).get(payment_id=payment_id)


        update_data = { 
            "is_delete" :   1
        }

        payment_ser     =   PaymentSerializer(instance=payment_record,data=update_data,partial=True)

        if payment_ser.is_valid():
            payment_ser.save()
            return JsonResponse({
                "success"     :   1,
                "message"     :   "record deleted",
            })
       






import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(['POST'])
def checkout_session(request):

    if settings.DEBUG:
        domain = "http://192.168.1.2:8000" 
    
    pass
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
               'price_data': 
                    {
                    'currency': 'inr',
                    'product_data': {
                        'name': 'paymant to openup',
                        },
                    'unit_amount': 10000,
                    },
                'quantity': 1,
            }],
        mode='payment',
        success_url=domain + '/success/',
        cancel_url=domain + '/cancel/',
    )
    return redirect(checkout_session.url)





def payment_success(request):
    return True




def payment_failed(request):
    return True
















