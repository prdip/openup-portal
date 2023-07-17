# Create your views here.
from rest_framework.decorators import api_view


# import Json Response
from django.http.response import JsonResponse, HttpResponseBadRequest

# Import token verifications
from openup_api.views.auth_views import token_verification
from datetime import datetime
from django.utils import timezone

import requests
import json
from django.http import HttpRequest
#  Import Serializer
from openup_app.serializers import PaymentFailedInfoSerializer
from openup_app.models import Registration, PaypalInfo, WebhookData,Jobs, Payment
from django.views.decorators.csrf import csrf_exempt

# import Payments class 
from openup.background_paypal import Payments

from openup.paypal_first_payment import First_PayPal_Payment

from celery import shared_task
# from openup.background_paypal import backgoun

import environ 
env = environ.Env()
environ.Env.read_env()


# Import Serializer
from openup_app.serializers import JobsSerializer   



@api_view(['POST'])
def apple_pay(request):
    
    
    payloads =  {
        "countryCode": 'US',
        "currencyCode": 'USD',
        "total": {
        "label": 'My Store',
        "amount": '10.00',
    },
  };
    
    request.data.get('validation_url')

    request.POST('https://apple-pay-gateway.apple.com/paymentservices/paymentSession')

    return JsonResponse({
            'status': 'success',
            # Include any additional required information
        })





@api_view(['POST'])
def process_payment(request):


    payment_token   =   request.data.get('payment_token')
    
    
    return JsonResponse({
            'status': 'success',
            # Include any additional required information
        })
    
    
    
