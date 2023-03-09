
# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse


# Import token verifications
from openup_api.views.auth_views import token_verification

import datetime 

from datetime import datetime

# Import Models here
from openup_app.models import Payment

# Import Serializer
from openup_app.serializers import PaymentSerializer

# Import validation
from .validation import check_text,check_number





# Api for add and edit data

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

            # validates card number
            check_card_no = check_number(card_no)
            if check_card_no is False:
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Please provide valid cvv ",
                        })

            # check card present
            try:
                check_card  =   Payment.objects.exclude(is_delete=1).filter(card_no=card_no).exists()
            except:
                check_card  =   False

            if check_card:
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "card number already exists "
                        })
            # check cvv provided or not
            if  card_cvv is None or card_cvv == "":
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Please provide cvv card number ",
                        })
            # Validates cvv contains numbers only

            check_cvv = check_number(card_cvv)
            if check_cvv is False:
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Please provide valid cvv ",
                        })

            # check for card holder name 

            if card_holder_name is None or card_holder_name ==  "":
                return JsonResponse({
                                "success"     :   0,
                                "message"     :   "Please provide card holder name ",
                        })

            # validates card holder name 
            check_name = check_text(card_holder_name)
            if check_name is False:
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
            validity = (datetime.strptime(card_validity,"%Y-%m-%d")).strftime("%Y-%m-%d")

            # card data to be added
            card_data = {
            "user_card_no"      :   card_no,
            "card_cvv"          :   card_cvv,
            "card_name"         :   card_holder_name,
            "card_validity"     :   validity,
            "card_type"         :   card_type,
            "created_at"        :   created_at
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

            # creates empty dict
            update_data = { }

            if card_no is not None:
                update_data["user_card_no"] =  card_no

            if card_cvv is not None:
                update_data["card_cvv"] =  card_cvv

            if card_holder_name is not None:
                update_data["card_name"] =  card_holder_name

            if card_validity is not None:
                update_data["card_validity"] =  card_validity

            if card_type is not None:
                update_data["card_type"] =  card_type

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

        # Get payment details
        payment_record  =   Payment.objects.exclude(is_delete=1).get(payment_id=payment_id)
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
       




