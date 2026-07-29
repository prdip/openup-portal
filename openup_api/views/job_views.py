# IMPORT CELERY
from openup import celery_app
 
import json

# IMPORT GEODESIC FROM GEOPY
from geopy.distance import geodesic as gd

# Create your views here.
from rest_framework.decorators import api_view

# IMPORT SOCKET
import socket,datetime,math

# IMPORT TASK HERE
from openup.fcm import FCM

# import Payments class 
from openup.payment import Payments

from openup.background_paypal import PaypalPayment

# import Json Response
from django.http.response import JsonResponse

# Import token verifications
from openup_api.views.auth_views import token_verification

# Import Models here
from openup_app.models import Registration,JobsType,Jobs,Alerts,VehicleDetails,Payment,PaypalInfo,PaymentFailedInfo,SuccessPayments, JobLogs, Images, File

# Import Serializer
from openup_app.serializers import JobsSerializer

# Import pillow
from PIL import Image

# Import Q
from django.db.models import Q

# IMPORT SHARED TASK
from celery import shared_task

from .validation import check_number,check_text

from django.utils import timezone

import logging
logger = logging.getLogger('django.request')

import requests

# PAYPAL HOST HELPERS
from openup.paypal_api import paypal_url, get_vault_record

# VENMO CHARGES THE VAULTED VENMO ACCOUNT, SEE venmo_views.py
from openup_api.views.venmo_views import venmo_payment
 
import environ 
env = environ.Env()
environ.Env.read_env()
'''
    ADD NEW JOB
IF CLIENT NOT VERIFIED IT WILL NOT ABLE TO ADD JOB
NOTIFY EMPLOYEE JOB IS ADDED 
AND PAYMENT WILL GENERATED IN BACKGROUND

'''



# SET CLIENT ID AND SECRET IN .ENV FILE

client_id=env("CLIENT_ID")
client_secret=env("CLIENT_SECRET")




 
@api_view(['POST'])
def add_job(request):
    #  Token Verification
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
        # required data
        job_type                =   request.data.get('job_type',None)
        current_location_lat    =   request.data.get('latitude',None)
        current_location_long   =   request.data.get('longitude',None)
        # vehicle_details         =   request.data.get('vehicle_details',None)
        # vehicle_modification    =   request.data.get('vehicle_modification',None)
        license                 =   request.data.get('vehicle_license',None)
        created_at              =   datetime.datetime.now()
        licence_name            =   request.data.get('licence_name',None)
        vehicle_id              =   request.data.get('vehicle_id',None)

        year        =   request.data.get('year')
        model       =   request.data.get('model')
        colour      =   request.data.get('colour')
        any_mod     =   request.data.get('any_mod')    # 1 === > Mod    0==> No mod
        window_tint =   request.data.get('window_tint') # 1 === > Yes    0==> No
        paypal_req_id = request.data.get('paypal_req_id')
        make         = request.data.get('make')
        payment_type = request.data.get('payment_type')
        payment_intent_id = request.data.get('payment_intent_id')   # APPLE PAY INTENT RETURNED BY /apple-pay

        if make == '' or make == None:
            return JsonResponse({
                    "success"    :   0,
                    "message"   :   "please provide string in make"
                    })

        if year == None or (year == ''):
            return JsonResponse({
                    "success"    :   0,
                    "message"   :   "please provide year"
                    })
        check_yr = check_number(year)
        if check_yr == False:
            return JsonResponse({
                    "success"    :   0,
                    "message"   :   "please provide number in year"
                    })


        if model == None or (model == ''):
            return JsonResponse({
                    "success"    :   0,
                    "message"   :   "please provide car model"
                    })
        
        if colour == None or (colour == ''):
            return JsonResponse({
                    "success"    :   0,
                    "message"   :   "please provide colour of car"
                    })
        
        check_col = check_text(colour)
        if check_col ==False:
            return JsonResponse({
                    "success"    :   0,
                    "message"   :   "please provide colour of car"
                    })


        if window_tint == None or (window_tint == ''):
            return JsonResponse({
                    "success"    :   0,
                    "message"   :   "please provide window tint or not"
                    })


        # job type accepts only employee and emergency

        if job_type is None or job_type == "" or (job_type != "service" and job_type != "emergency"):
            return JsonResponse({
                    "success"    :   0,
                    "message"   :   "please provide job type"
                    })
        
        if current_location_lat == None or current_location_lat ==  "":
            return JsonResponse({
                    "success"    :   0,
                    "message"   :   "please provide current location "
                    })
        
        if current_location_long is None or current_location_long == "":
            return JsonResponse({
                    "success"    :   0,
                    "message"   :   "please provide current location "
                    })

       
        user_id     =       check_user['session_user']

       
        if vehicle_id == None and license ==  None:
            # No id No image
            license = None

        elif license == None and vehicle_id != None:
            #  Old id and No image
            try:
                    veh_rec  =   VehicleDetails.objects.get(vehicle_id=int(vehicle_id))     
            except:
                    veh_rec  =   None

            if veh_rec == None:
                license     =    None
            else:
                license     =    veh_rec.vehicle_license

        elif license != None and vehicle_id == None:
                # New image No id 
            try:
                    im = Image.open(license)
            except:
                    im = None
            if im == None: 
                    return JsonResponse({
                        "success"     :   0,
                        "message"     :   "Please provide valid image",
                    })

        # id and new image
        else:                
            try:
                    im = Image.open(license)
            except:
                    im = None
            if im == None: 
                    return JsonResponse({
                        "success"     :   0,
                        "message"     :   "Please provide valid image",
                    })
           
        # get user id from token
        
        # get instance of login user
        user_rec    =       Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)

        try:
            paypal = PaypalInfo.objects.filter(paypal_user = user_rec.user_id).exists()
        except:
            paypal = False
    
        try:
            stripe = user_rec.user_stripe_id
        
        except:
            stripe = None
        
        try:
            payment_id = user_rec.user_payment_id
        except:
            payment_id = None

        '''
        APPLE PAY IS PAID UP FRONT BY /apple-pay, WHICH PARKS THE SUCCESSFUL INTENT
        WITH AN EMPTY pay_job. AN UNCLAIMED PAYMENT IS WHAT ALLOWS THE JOB HERE.
        '''
        apple_payment   =   SuccessPayments.objects.filter(pay_user=str(user_rec.user_id),pay_type="apple_pay",pay_job="")
        if payment_intent_id != None and payment_intent_id != "":
            apple_payment = apple_payment.filter(pay_response__contains=payment_intent_id)
        apple_payment   =   apple_payment.order_by('pay_id').last()

        if paypal == False and apple_payment == None and (stripe == None or payment_id == None):
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "You are not allow to add job",

                })


        if user_rec.user_is_verified == 0:
             return JsonResponse({   
                "success"    :   0,
                "message"   :   "You are not allowed to add job! please verify email to use service ",
                })
        job_id      =       JobsType.objects.first()
        
        job_details = {
                "job_type"              :   job_type,
                "location_latitude"     :   float(current_location_lat),
                "location_longitude"    :   float(current_location_long),
                "vehicle_license"       :   license,
                "created_at"            :   created_at,
                "user"                  :   user_rec.user_id,
                "job_status"            :   job_id.status_id,
                "year"                  :   year,
                "model"                 :   model,
                "colour"                :   colour,
                "any_mod"               :   any_mod,
                "window_tint"           :   window_tint,      
                "make"                  :   make   
        }
        job_ser     =   JobsSerializer(data=job_details)

        # get serializer data
        if job_ser.is_valid():
            # com now
            id = job_ser.save()
            '''
                JOB ALERT IS SHARED TASK FUNCTION RUN IN BACKGROUND @shardtask decorator required
            '''
            accepted_by = ''
            jobAlert(id,current_location_lat,current_location_long,accepted_by)
             
            # payment_type = user_rec.user_payment_type

            if payment_type == "stripe":
                 
                # '''Payment code '''
                background_payment.delay(user_id,id)

    
            if payment_type=="paypal":

                    data = {
                        "user"          :   user_id,
                        "job_id"        :   id,
                        "paypal_req_id" :   paypal_req_id,

                    }

                    paypal_payment.delay(data)

            if payment_type == "venmo":
                '''
                THE VENMO ACCOUNT WAS ALREADY APPROVED AND VAULTED BY
                /api/venmo-setup + /api/venmo-confirm, SO THIS IS A PLAIN
                MERCHANT INITIATED CHARGE - NO BUYER INTERACTION HERE.
                '''
                data = {
                    "user"          :   user_id,
                    "job_id"        :   id,
                    "paypal_req_id" :   paypal_req_id,
                }

                venmo_payment.delay(data)

            if payment_type == "apple_pay" and apple_payment != None:
                '''
                MONEY IS ALREADY TAKEN BY /apple-pay SO NO CHARGE IS RAISED HERE,
                THE PARKED PAYMENT IS ONLY CLAIMED BY THIS JOB
                '''
                intent_id = payment_intent_id
                if intent_id == None or intent_id == "":
                    try:
                        intent_id = json.loads(apple_payment.pay_response)['id']
                    except:
                        intent_id = None

                apple_payment.pay_job = str(id)
                apple_payment.save()

                job_record  =   Jobs.objects.exclude(is_delete=1).get(job_id=int(id))
                paid_data   =   {
                        "job_payment_id"    :   intent_id,
                        "job_pay_status"    :   1,
                }
                paid_ser    =   JobsSerializer(instance=job_record,data=paid_data,partial=True)
                if paid_ser.is_valid():
                    paid_ser.save()

            if job_type == "emergency" and payment_type != "apple_pay":
                #    comment now
                pay_type     = SuccessPayments.objects.filter(pay_user = user_id).order_by('pay_id').reverse()[:1] 
                try:
                    payment = pay_type.values('pay_type').first()['pay_type']

                except:
                    payment = None

                if payment == "stripe":
                    
                    # '''Payment code '''
                    background_payment.delay(user_id,id)

                if payment=="paypal":


                        data = {
                            "user"          :   user_id,
                            "job_id"        :   id,
                            "paypal_req_id" :   paypal_req_id,

                        }
                        paypal_payment.delay(data)

                if payment == "venmo":

                        data = {
                            "user"          :   user_id,
                            "job_id"        :   id,
                            "paypal_req_id" :   paypal_req_id,
                        }
                        venmo_payment.delay(data)
                # after if
            data = {
                        "job_id" : id,
                    }
             
            return JsonResponse({
                "success"   :   1,
                "message"   :   "Job added successfully",
                "data"      :   data
                })
        else:
            return JsonResponse({   
                "success"   :   0,
                "message"   :   "error occured",
                "error"     :   job_ser.errors
                })
              
       
# WORKING CODE OF LIVE
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





# WORKING CODE OF LIVE
# RECURRING PAYPAL PAYMENT

@shared_task()
def paypal_payment(data):
        

        job_id           =   data['job_id']
        paypal_req_id   =   data['paypal_req_id']  # random text
        login_user      =   data['user']
        paypal_data     =   get_vault_record(login_user,'card')
        user            =   Registration.objects.get(user_id=login_user)

        '''NOTHING VAULTED MEANS THERE IS NOTHING TO CHARGE - RECORD IT INSTEAD OF CRASHING'''
        if paypal_data is None:
            logger.error('paypal_payment: No vaulted card for user %s (job %s)', login_user, job_id)
            PaymentFailedInfo(
                user_id=login_user,
                job_id=job_id,
                payment_fail_type="no_vault",
                payment_fail_response="No vaulted paypal card found for this user",
                created_at=timezone.now()
            ).save()
            return False

        # get access token
        url             =   paypal_url('/v1/oauth2/token')
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

        # # Send payment request WORKING CODE OF LIVE
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

























'''
 JobAlert function calls whenever new job added by client

 latitude and longitude pass by client 

 SERVICE_JOB == >  ALERT TO ACTIVE EMP
 EMERGENCY_JOB ==> ALERT TO ACTIVE AND INACTIVE EMP

'''
# @shared_task()
def jobAlert(job_id,latitude,longitude,accepted_by):
    # Fetch Employee List

    job_instance    =    Jobs.objects.exclude(is_delete=1).get(job_id=int(job_id))

    # Build list of employee IDs to exclude (accepted_by + all previously attempted)
    excluded_ids = set()
    if accepted_by:
        excluded_ids.add(int(accepted_by))
    attempted = job_instance.job_attempted_by or ''
    for aid in attempted.split(','):
        aid = aid.strip()
        if aid:
            excluded_ids.add(int(aid))

    if not excluded_ids:
        if job_instance.job_type == "emergency":
            
            employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).filter(user_role_id=1)
            message     =  "EMERGENCY!!! PLEASE ACCEPT THIS JOB ASAP!!!"

        else:
            employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).filter(employee_status=1).filter(user_role_id=1)
            message     =  "PLEASE ACCEPT THIS JOB ASAP!!!"
    else:
        if job_instance.job_type == "emergency":
        
            employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).exclude(user_id__in=excluded_ids).filter(user_role_id=1)
            message     =  "EMERGENCY!!! PLEASE ACCEPT THIS JOB ASAP!!!"

        else:
            employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).exclude(user_id__in=excluded_ids).filter(employee_status=1).filter(user_role_id=1)
            message     =  "PLEASE ACCEPT THIS JOB!!!"


    # employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).filter(user_role_id=1)

    # get employee list
    user_list   =   []
    emp_fcm     =   []
    emplist     =   {}
    data        =   {}
    '''IN EMPLOYEE DICT   KEY == > EMPLOYEE_ID  VALUE_LIST ==> [FCM,DEVICE TYPE]'''
    for employee in employees:
        if employee.user_fcm_token != "" or employee.user_fcm_token != None: 
            # user location
            user_location = (latitude,longitude)
            # employee location
            emp_location =  (employee.location_latitude,employee.location_longitude)
            # calculate distance between two point 
            # dist        =   gd(user_location,emp_location).km
            api_key  =  'AIzaSyC2o6UvDF6qUUQM3KCwR6dwoV5qCfj8MGs'
            url      =  f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={latitude},{longitude}&destinations={employee.location_latitude},{employee.location_longitude}&key={api_key}"
            response =  requests.get(url)
            data     =  response.json()

            try:
                duration_seconds = data['rows'][0]['elements'][0]['duration']['value']
            except KeyError:
                duration_seconds =''


            # if dist is less than 6 km append list 
            if duration_seconds != '':
                if int(duration_seconds) <= 1260:
                    user_list.append(employee.user_id)

                    emp_fcm.append(employee.user_fcm_token)
                    emplist[str(employee.user_id)] = list((str(employee.user_fcm_token),str(employee.device_type))) 

    if len(user_list) == 0:
        client_fcm = job_instance.user.user_fcm_token
        noti_data={ }  
    
        data = { 
             'title'                      :     'Not Accepted',             
             'notificationScreenType'     :     'addjob',
             'message'                    :     'We are currently not available in your area. Coming soon',
             'job_id'                     :     str(job_id),  
             'job_type'                   :     job_instance.job_type
            }
        noti_data['fcm_token']  =   client_fcm 
        noti_data['device']     =   str(employee.device_type)
        noti_data['data']       =   data
        
        job_status      = JobsType.objects.get(status_id=5)
        update_record   = {
            "job_status" : job_status.status_id 
            }

        job_serializer = JobsSerializer(instance=job_instance,data=update_record,partial=True)
        if job_serializer.is_valid():
           
            job_serializer.save()
    
        # sends push notification
        FCM.send_notification(noti_data)
        return True
    
    emp_lis         =   ','.join(str(i) for i in user_list)
    alert_title     =    "new job added"
    alert_messages  =    "job generated"
    created_at      =     timezone.now()
    
    # Alert Table Save entry
    data            =   Alerts(alert_job=job_instance, alert_users=emp_lis,alert_title=alert_title,
                             alert_messages=alert_messages,
                            created_at=created_at) 
    data.save() 
    noti_data={ }  

    # pass dictionary data to send notification
    not_data = { 
             'title'                      :     'New job request',             
             'notificationScreenType'     :     'addjob',
             'message'                    :     message,
             'job_id'                     :     str(job_id),  
             'job_type'                   :     job_instance.job_type
            }
             
    job_status      = JobsType.objects.get(status_id=1)
    update_record   = {
        "job_status" : job_status.status_id 
        }

    job_serializer = JobsSerializer(instance=job_instance,data=update_record,partial=True)
    if job_serializer.is_valid():
        job_serializer.save()

    # SEND NOTIFICATIONS 

    for employee in user_list:

        employee = Registration.objects.exclude(Q(user_is_delete=1)).get(user_id=employee)
        if employee.user_fcm_token!=None and employee.user_fcm_token!='':
            noti_data['data']       =   not_data
            noti_data['fcm_token']  =   employee.user_fcm_token 
            noti_data['device']     =   str(employee.device_type)
            # sends push notification
            FCM.send_notification(noti_data)
     

    return True
    



'''

function that removes data from list

'''
def removeElements(items,lists):
    for dict in lists:
        for item in items:
            del(dict[item])
    return lists


'''
HELPER: LIST OF EMPLOYEE IDS THAT ALREADY ACTED (REJECTED/CANCELLED) ON A JOB
'''
def attempted_ids(job_record):
    attempted = job_record.job_attempted_by or ''
    return [x.strip() for x in attempted.split(',') if x.strip()]


'''
HELPER: TRUE WHEN THE EMPLOYEE ALREADY REJECTED OR CANCELLED THIS JOB
'''
def has_attempted(job_record,user_id):
    return str(user_id) in attempted_ids(job_record)


'''
HELPER: TRUE WHEN THE EMPLOYEE WAS NOTIFIED (ALERTED) ABOUT THIS JOB.

jobAlert() persists every alert in the Alerts table with the comma separated list
of employees it notified, so the notification state survives the app being closed.
Legacy jobs created before alerts were stored have no Alerts row, those are treated
as visible to every employee so they are not lost.
'''
def was_alerted(job_record,user_id):
    alerts = Alerts.objects.exclude(is_delete=1).filter(alert_job=job_record.job_id)

    if not alerts.exists():
        return True

    for alert in alerts:
        users = [x.strip() for x in (alert.alert_users or '').split(',') if x.strip()]
        if str(user_id) in users:
            return True

    return False


'''
HELPER: BUILDS THE JOB DETAIL PAYLOAD (SHARED BY job_details AND active_job)
'''
def build_job_payload(job_data):

    # send instance to serializer
    job_serializer  =   JobsSerializer(job_data).data
    # remove field from dict
    job_serializer.pop('created_at')
    job_serializer.pop('is_delete')

    # create image url

    if job_serializer['vehicle_license'] != None:
        domain      =      env('BASE_URL')
        obj         =       job_serializer['vehicle_license']
        url         =       '{domain}{path}'.format(domain=domain, path=obj)

        job_serializer['vehicle_license_url'] = url

    if job_serializer['job_pay_status'] == True:
        job_serializer['job_pay_status'] = "1"
    else:
         job_serializer['job_pay_status'] = "0"

    if job_serializer['job_status'] == 1:
        job_serializer['job_status'] = "active"

    if job_serializer['job_status'] == 2:
        job_serializer['job_status'] = "accepted"

    if job_serializer['job_status'] == "3":
        job_serializer['job_status']="completed"

    if job_serializer['job_status'] == "4":
        job_serializer['job_status']="not accepted"

    if job_serializer['any_mod'] == True:
         job_serializer['any_mod'] = "1"
    else:
         job_serializer['any_mod'] = "0"


    if job_serializer['window_tint'] == True:
         job_serializer['window_tint'] = "1"
    else:
         job_serializer['window_tint'] = "0"

    # if block execute when job_accepted_by in job record is null
    if job_data.job_accepted_by != None:

        try:
            user_record = Registration.objects.exclude(user_is_delete=1).get(user_id=job_data.job_accepted_by)
        except:
            user_record = None

        if user_record != None:
            '''to get employee name '''
            job_serializer['employee_name'] = user_record.user_first_name+' '+user_record.user_last_name

    domain =  env('BASE_URL')
    images = Images.objects.exclude(is_delete=1).filter(job=int(job_data.job_id)).exists()
    if images:

        img_id_list = Images.objects.exclude(is_delete=1).filter(job=job_data.job_id)

        imges_list  = []
        before_list = []
        after_list = []
        img_dict   = {}
        for image in img_id_list:

            if image.img_type == 1:

                files  = File.objects.exclude(is_delete=1).filter(file_img=image.img_id).exists()

                if files:
                    files_list = File.objects.exclude(is_delete=1).filter(file_img=image.img_id)

                    for file in files_list:

                        image = domain + file.file.url
                        before_list.append(image)
            else:

                files  = File.objects.exclude(is_delete=1).filter(file_img=image.img_id).exists()

                if files:
                    files_list = File.objects.exclude(is_delete=1).filter(file_img=image.img_id)

                    for file in files_list:

                        image = domain + file.file.url
                        after_list.append(image)


        img_dict['type']   = 'Before'
        img_dict['images'] = before_list
        imges_list.append(img_dict)
        img_dict1 ={}
        img_dict1['type']   = 'After'

        img_dict1['images']  = after_list
        imges_list.append(img_dict1)
        job_serializer['images'] = imges_list

    job_serializer.pop('vehicle_license')

    return job_serializer



 
'''
API to Get detail of job by job id 
'''

@api_view(['POST'])
def job_details(request):
    #  Token Verification
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')  
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })
    
    # if token verified m
    else:
        # required data
        user_id     =       check_user['session_user']
        job_id      =       request.data.get('job_id',None)
        
        # check if jon id is blank
        if job_id is None or job_id == "":
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Please provide job id",
            })
        
        # get job instance using if
        try:  
            job_data        =   Jobs.objects.exclude(is_delete=1).get(job_id=job_id)
        except:
            job_data        =   None
        
        if job_data==None:
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Please provide job id",
            })

        if job_data.job_status_id == 4:
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "This job has been cancelled",
            })

        if job_data.job_accepted_by != None: 
            if int(job_data.job_accepted_by) != int(user_id):
                return JsonResponse({
                    "success"     :   0,
                    "message"     :   "This job is accepted by another employee"
                })

        job_serializer  =   build_job_payload(job_data)

        data = {
            "job_details":job_serializer
        }
        return JsonResponse({
                    "success"     :   1,
                    "message"     :   "Job details fetched",
                    "data"        :     data
                    })
    




@api_view(['POST'])
def remove_job(request):

    token       = request.headers['Authorization']
    user_token  = token.replace("Bearer",'')  
    check_user  = token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
                })
    
    # if token verified
    else:
        # # required data
        job_id      =       request.data.get('job_id',None)

        # check if job id is blank
        if job_id is None or job_id == "":
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Please provide job id",
                })
        
        update_data     =   {
                 "is_delete"     :       1
                }
        # JOB INSTANCE
        job_data        =   Jobs.objects.exclude(is_delete=1).get(job_id=job_id)
        job_serializer  =   JobsSerializer(data=update_data,instance=job_data,partial=True)
       
        if job_serializer.is_valid():
            job_serializer.update(update_data)
            return JsonResponse({
                    "success"     :   1,
                    "message"     :   "Record removed successfully",
                 })
        else:
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Record removed successfully",
                    "job_serializer":   job_serializer.errors
                })






'''API to ACCEPT JOB.  job accepted by employee '''

@api_view(['POST'])
def accept_job(request):

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
        # required data
        job_id          =       request.data.get('job_id',None)
        user_id         =       check_user['session_user']
        user_record     =       Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
        try:
            job_record =        Jobs.objects.exclude(is_delete=1).get(job_id=job_id)

        except:
            job_record = None
        
        if job_record is None:
            return JsonResponse({
                            "success"     :   0,
                            "message"     :   "Please enter valid job id",
                    })

        if job_record.job_status_id == 2 or job_record.job_status_id == 3:
            return JsonResponse({
                            "success"     :   0,
                            "message"     :   "Job already accepted",
                    })
        
        if  job_record.job_status_id==4:
             return JsonResponse({
                            "success"     :   0,
                            "message"     :   "Job already canceled by client",
                    })     
        data = {
            "job_status"     :   2,
            "job_accepted_by":  user_record.user_id
        }   
        job_serializer   = JobsSerializer(instance=job_record,data=data,partial=True)

        # DATA IN RESPONSE
        user_data        = {
            "first_name"            :       user_record.user_first_name,
            "middle_name"           :       user_record.user_middle_name,
            "last_name"             :       user_record.user_last_name,
            "email"                 :       user_record.user_email,
            "mobile_number"         :       user_record.user_phone_number,
            "location_latitude"     :       job_record.location_latitude,
            "location_longitude"    :       job_record.location_longitude
            }

        data = {
            "employee" :   user_data
        }
        if job_serializer.is_valid():
            job_serializer.save(**data)

            # Notification data
            accept_job_notification.delay(job_id)

            return JsonResponse({
                            "success"     :   1,
                            "message"     :   "Job accepted by employee",
                            "data"        :     data
                    })
        
        else:

            return JsonResponse({
                            "success"     :   0,
                            "message"     :   "some error occured",
                        })
        


#  Notification generate for accept job
'''
NOTIFY CLIENT THAT JOB ACCEPTED
''' 
@shared_task()
def accept_job_notification(job_id):

    user_id     = Jobs.objects.exclude(is_delete=1).get(job_id=int(job_id))
    user_record = Registration.objects.exclude(Q(user_is_delete = 1) and Q(user_role_id=1)).get(user_id=user_id.user_id)
    # User information dictionary
    data = { 
            'title'                             :   'job acepted',
            'notificationScreenType'            :   "acceptjob",
            'message'                           :   'Your job accepted',
            'job_id'                            :    job_id
        }
    # SEND NOTIFICATIONS 

    noti_data={ }  
    noti_data['data']       =   data
    noti_data['fcm_token']  =   str(user_record.user_fcm_token)
    noti_data['device']     =   str(user_record.device_type)
    
    FCM.send_notification(noti_data)     
    return True


    


'''API FOR REJECT JOB'''
@api_view(['POST'])
def reject_job(request):

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
        # job_id      =       request.data.get(job_id,None)
        return JsonResponse({
            "success"   :    1,
            "message"   :   "job rejected"
            })






'''API FOR COMPLETE JOB 
JOB_STATUS WILL CHANGE TO 3
AND NOTIFY CLIENT THAT JOB IS COMEPLETED
'''
@api_view(['POST'])
def complete_job(request):
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

        job_id      =       request.data.get("job_id",None)
        user_id     =       check_user['session_user']
        try:
            job_record  =       Jobs.objects.exclude(Q(job_status=1) and Q(job_status=3) and Q(is_delete=1)).get(job_id=job_id)
        except:
            job_record  =   None


        if job_record == None:
            return JsonResponse({
                "success"   :   0,
                "message"   :   "No record found"
            })
        
        if job_record.job_status_id == 3:
            return JsonResponse({
                "success"   :   0,
                "message"   :   "Job already completed"
            })
        
        if job_record.job_status_id == 4:
                return JsonResponse({
                "success"   :   0,
                "message"   :   "job is already canceled by client"
                })
        job_accepted_by = job_record.job_accepted_by

        if job_accepted_by == None or user_id != int(job_record.job_accepted_by):
            return JsonResponse({
                "success"   :   0,
                "message"   :   "invalid employee"
            })
       

        job_status      = JobsType.objects.get(status_id=3)
        update_record   = {
            "job_status" : job_status.status_id 
            }

        job_serializer = JobsSerializer(instance=job_record,data=update_record,partial=True)
        if job_serializer.is_valid():
            job_serializer.save()
            
            # complete job notification function 
            complete_job_notification.delay(job_id)

            if job_record.job_pay_status == True:
                job_pay_status = 1 
            else:
                 job_pay_status = 0

            data = {
                "job_payment_status"    :       job_pay_status
            }

            return JsonResponse({
                "success"   :   1,
                "message"   :   "job completed",
                "data"      :    data

                })
        else:
            return JsonResponse({
                "success"   :   0,
                "message"   :   "error occured"
                })




''' NOTIFY CLIENT THAT JOB IS COMPLETED '''
@shared_task()
def complete_job_notification(job_id):

    try:
        client_id   =   Jobs.objects.exclude(Q(job_status=1) and Q(job_status=3) and Q(job_status=4)).filter(job_id=job_id).values('user_id').first()['user_id']

    except:

        client_id   =   None

    
    client_record   =   Registration.objects.exclude(user_is_delete=1).get(user_id=client_id)
    
    # User information dictionary

    data = { 
            'title'                    :   'job completed',
            'notificationScreenType'    :   "completejob",
            'message'                   :   'Your job completed. Please add review about your job',
            'job_id'                    :   job_id
        }
        
    
    # SEND NOTIFICATIONS 

    noti_data={ }  
    noti_data['data'] = data
    noti_data['fcm_token']  =  (str(client_record.user_fcm_token))
    noti_data['device']     =  str(client_record.device_type)
    
    FCM.send_notification(noti_data)
    return True







'''API FOR CANCEL JOB'''
@api_view(['POST'])
def cancel_job(request):

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
        user_id     =   check_user['session_user']

        job_id      =   request.data.get('job_id')

      
        try:
            job_record  =   Jobs.objects.exclude(is_delete=1).get(job_id=int(job_id))
        except:
            job_record = None


        if job_record == None:
             return JsonResponse({
                "success"     :   0,
                "message"     :   "no job found",
                })
         
        if job_record.job_status.status_id==4:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "job is already canceled",
                })

        # Track the employee who had accepted (if any) in job_attempted_by
        existing_attempted = job_record.job_attempted_by or ''
        if job_record.job_accepted_by:
            emp_id_str = str(job_record.job_accepted_by)
            if emp_id_str not in [x.strip() for x in existing_attempted.split(',') if x.strip()]:
                if existing_attempted:
                    new_attempted = existing_attempted + ',' + emp_id_str
                else:
                    new_attempted = emp_id_str
            else:
                new_attempted = existing_attempted
        else:
            new_attempted = existing_attempted

        update_data = {
            "job_status_id" : 4,
            "job_accepted_by" : None,
            "job_attempted_by" : new_attempted
        }

        job_ser = JobsSerializer(instance=job_record,data=update_data,partial=True)

        if job_ser.is_valid():
            job_ser.save()

            cancel_job_notification.delay(job_id)


            return JsonResponse({
                    "success"     :   1,
                    "message"     :   "Your job is cancelled",
                    })
        else:
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "some error occured",
                    })

    
    


'''Notify all employees that the job has been cancelled'''
@shared_task()
def cancel_job_notification(job_id):
     # Fetch Employee List

    job_instance    =    Jobs.objects.exclude(is_delete=1).get(job_id=int(job_id))

    if job_instance.job_type == "emergency":
        
        employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).filter(user_role_id=1)
    else:
        employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).filter(employee_status=1).filter(user_role_id=1)

    # employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).filter(user_role_id=1)

    # get employee list
    user_list   =   []
    emp_fcm     =   []
    emplist     =   {}
    data        =   {}
    '''IN EMPLOYEE DICT   KEY == > EMPLOYEE_ID  VALUE_LIST ==> [FCM,DEVICE TYPE]'''
    for employee in employees:
        if employee.user_fcm_token != "" or employee.user_fcm_token != None: 
            # user location 
            user_list.append(employee.user_id)
            emp_fcm.append(employee.user_fcm_token)
            emplist[str(employee.user_id)] = list((str(employee.user_fcm_token),str(employee.device_type))) 
  
 
    noti_data={ }  

    # pass dictionary data to send notification
    not_data = { 
             'title'                      :     'Cancel Job',             
             'notificationScreenType'     :     'cancel_job',
             'message'                    :     'The job has been cancelled',
             'job_id'                     :     str(job_id),  
             'job_type'                   :     job_instance.job_type
            }
             
    # SEND NOTIFICATIONS 
    
    for employee in employees:
        if employee.user_fcm_token!=None and employee.user_fcm_token!='':
            noti_data['data']       =   not_data
            noti_data['fcm_token']  =   employee.user_fcm_token 
            noti_data['device']     =   str(employee.device_type)
            # sends push notification
            FCM.send_notification(noti_data)
     
    return True



'''API FOR CANCEL JOB by employee'''
@api_view(['POST'])

def cancel_job_by_employee(request):
    try:
        token       = request.headers['Authorization']
    except KeyError:
        logger.error('cancel_job_by_employee: Missing Authorization header')
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Missing Authorization header",
                })

    user_token  = token.replace("Bearer",'')  
    check_user  = token_verification(user_token)

    if check_user is None:
        logger.warning('cancel_job_by_employee: Unauthorized access attempt')
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
                })
    
    # if token verified
    else:
        job_id  = request.data.get('job_id')
        user_id = check_user['session_user']

        if job_id is None or job_id == '':
            logger.warning('cancel_job_by_employee: Missing job_id by user %s', user_id)
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide a valid job id",
                })

        try:
            job_id = int(job_id)
        except (ValueError, TypeError):
            logger.warning('cancel_job_by_employee: Invalid job_id format "%s" by user %s', job_id, user_id)
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Invalid job id format",
                })

        try:
            job_record  =   Jobs.objects.exclude(is_delete=1).get(job_id=job_id)
        except Jobs.DoesNotExist:
            logger.warning('cancel_job_by_employee: Job %s not found (user %s)', job_id, user_id)
            return JsonResponse({
                "success"     :   0,
                "message"     :   "No job found with the given id",
                })
        except Exception as e:
            logger.error('cancel_job_by_employee: DB error fetching job %s: %s', job_id, str(e))
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Database error while fetching job",
                })

        status_id = job_record.job_status.status_id

        if status_id == 1:
            logger.info('cancel_job_by_employee: Job %s already active/canceled (user %s)', job_id, user_id)
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Job is already canceled",
                })

        if status_id == 4:
            logger.info('cancel_job_by_employee: Job %s already canceled by client (user %s)', job_id, user_id)
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Job is already canceled by the client",
                })

        if status_id == 3:
            logger.info('cancel_job_by_employee: Job %s already completed, cannot cancel (user %s)', job_id, user_id)
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Job is already completed and cannot be canceled",
                })

        if status_id == 5:
            logger.info('cancel_job_by_employee: Job %s has no available employees (user %s)', job_id, user_id)
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Job has no available employees",
                })

        if job_record.job_accepted_by is None or int(job_record.job_accepted_by) != int(user_id):
            logger.warning('cancel_job_by_employee: User %s is not the acceptor of job %s (accepted_by=%s)', user_id, job_id, job_record.job_accepted_by)
            return JsonResponse({
                "success"     :   0,
                "message"     :   "You are not authorized to cancel this job",
                })

        accepted_by = job_record.job_accepted_by

        # Append cancelling employee to job_attempted_by
        existing_attempted = job_record.job_attempted_by or ''
        if str(user_id) not in [x.strip() for x in existing_attempted.split(',') if x.strip()]:
            if existing_attempted:
                new_attempted = existing_attempted + ',' + str(user_id)
            else:
                new_attempted = str(user_id)
        else:
            new_attempted = existing_attempted

        update_data = {
            "job_status_id" : 1,
            "job_accepted_by" : None,
            "job_attempted_by" : new_attempted
        }

        try:
            job_log = JobLogs(
                job=job_record.job_id,
                log_msg="Job canceled by employee",
                cancel_by=accepted_by,
                created_at=timezone.now()
            ) 
            job_log.save()
        except Exception as e:
            logger.error('cancel_job_by_employee: Failed to save JobLogs for job %s: %s', job_id, str(e))
        
        job_ser = JobsSerializer(instance=job_record,data=update_data,partial=True)

        if job_ser.is_valid():
            try:
                job_ser.save()
            except Exception as e:
                logger.error('cancel_job_by_employee: Failed to save job update for job %s: %s', job_id, str(e))
                return JsonResponse({
                        "success"     :   0,
                        "message"     :   "Failed to update job status",
                        })

            try:
                notify_client.delay(job_id,user_id)
            except Exception as e:
                logger.error('cancel_job_by_employee: Failed to send notify_client task for job %s: %s', job_id, str(e))

            try:
                jobAlert(job_id,job_record.user.location_latitude,job_record.user.location_longitude,accepted_by)
            except Exception as e:
                logger.error('cancel_job_by_employee: Failed to run jobAlert for job %s: %s', job_id, str(e))

            logger.info('cancel_job_by_employee: Job %s canceled successfully by user %s', job_id, user_id)
            return JsonResponse({
                    "success"     :   1,
                    "message"     :   "Your job is cancelled by employee",
                    })
        else:
            logger.error('cancel_job_by_employee: Serializer errors for job %s: %s', job_id, job_ser.errors)
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Failed to update job due to validation error",
                    "error"       :   job_ser.errors
                    })

    

@shared_task()
def job_alert_after_cancel(job_id,latitude,longitude,accepted_by):
    job_instance    =    Jobs.objects.exclude(is_delete=1).get(job_id=int(job_id))
     
    if job_instance.job_type == "emergency":
        
        employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).exclude(job_accepted_by=accepted_by).filter(user_role_id=1)
        message     =  "EMERGENCY!!! PLEASE ACCEPT THIS JOB ASAP!!!"

    else:
        employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).exclude(job_accepted_by=accepted_by).filter(employee_status=1).filter(user_role_id=1)
        message     =  "PLEASE ACCEPT THIS JOB ASAP!!!"
    # employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).filter(user_role_id=1)

    # get employee list
    user_list   =   []
    emp_fcm     =   []
    emplist     =   {}
    data        =   {}
    '''IN EMPLOYEE DICT   KEY == > EMPLOYEE_ID  VALUE_LIST ==> [FCM,DEVICE TYPE]'''
    for employee in employees:
        if employee.user_fcm_token != "" or employee.user_fcm_token != None: 
            # user location
            user_location = (latitude,longitude)
            # employee location
            emp_location =  (employee.location_latitude,employee.location_longitude)
            # calculate distance between two point 
            # dist        =   gd(user_location,emp_location).km
            api_key  =  'AIzaSyC2o6UvDF6qUUQM3KCwR6dwoV5qCfj8MGs'
            url      =  f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={latitude},{longitude}&destinations={employee.location_latitude},{employee.location_longitude}&key={api_key}"
            response =  requests.get(url)
            data     =  response.json()
             
            try:
                duration_seconds = data['rows'][0]['elements'][0]['duration']['value']
            except KeyError:
                duration_seconds =''
            # if dist is less than 6 km append list 

            if duration_seconds <= 1260 and duration_seconds != '':
                user_list.append(employee.user_id)
                emp_fcm.append(employee.user_fcm_token)
                emplist[str(employee.user_id)] = list((str(employee.user_fcm_token),str(employee.device_type))) 

    if len(user_list) == 0:
        client_fcm = job_instance.user.user_fcm_token
        noti_data={ }  
    
        data = { 
             'title'                      :     'Not Accepted',             
             'notificationScreenType'     :     'addjob',
             'message'                    :     'We are currently not available in your area. Coming soon',
             'job_id'                     :     str(job_id),  
             'job_type'                   :     job_instance.job_type
            }
        
        noti_data['fcm_token']  =   client_fcm 
        noti_data['device']     =   str(employee.device_type)
        noti_data['data']       =   data

        # sends push notification

        FCM.send_notification(noti_data)

        job_status      = JobsType.objects.get(status_id=1)
        update_record   = {
            "job_status_id" : job_status.status_id 
            }

        job_serializer = JobsSerializer(instance=job_instance,data=update_record,partial=True)
        if job_serializer.is_valid():
            job_serializer.save()


        return True
    


'''Notify all employees that the job has been active again'''
@shared_task()
def notify_client(job_id,user_id):
    job_instance    =    Jobs.objects.exclude(is_delete=1).get(job_id=int(job_id))


    client_fcm = job_instance.user.user_fcm_token
    noti_data={ }  

    data = { 
            'title'                      :     'Job Cancelled by Employee. This job is active now',             
            'notificationScreenType'     :     'cancel_job',
            'message'                    :     'This job has been cancelled by the employee.Your job is active now',
            'job_id'                     :     str(job_id),  
            'job_type'                   :     job_instance.job_type
        }
    
    noti_data['fcm_token']  =   client_fcm 
    noti_data['device']     =   str(job_instance.user.device_type)
    noti_data['data']       =   data

    # sends push notification

    FCM.send_notification(noti_data)


    if job_instance.job_type == "emergency":
        
        employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).exclude(user_id=user_id).filter(user_role_id=1)
        message     =  "EMERGENCY!!! PLEASE ACCEPT THIS JOB ASAP!!!"

    else:
        employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).exclude(user_id=user_id).filter(employee_status=1).filter(user_role_id=1)
        message     =  "PLEASE ACCEPT THIS JOB ASAP!!!"

    # Build exclusion set from job_attempted_by
    excluded_ids = set()
    if user_id:
        excluded_ids.add(int(user_id))
    attempted = job_instance.job_attempted_by or ''
    for aid in attempted.split(','):
        aid = aid.strip()
        if aid:
            excluded_ids.add(int(aid))

    if excluded_ids:
        if job_instance.job_type == "emergency":
            employees = Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).exclude(user_id__in=excluded_ids).filter(user_role_id=1)
        else:
            employees = Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).exclude(user_id__in=excluded_ids).filter(employee_status=1).filter(user_role_id=1)
    # employees   =  Registration.objects.exclude(Q(user_is_delete=1) & Q(user_role_id=2)).filter(user_role_id=1)

    # get employee list
    user_list   =   []
    emp_fcm     =   []
    emplist     =   {}
    data        =   {}
    '''IN EMPLOYEE DICT   KEY == > EMPLOYEE_ID  VALUE_LIST ==> [FCM,DEVICE TYPE]'''
    for employee in employees:
        if employee.user_fcm_token != "" or employee.user_fcm_token != None: 
            # user location
            user_location = (job_instance.location_latitude,job_instance.location_longitude)
            # employee location
            emp_location =  (employee.location_latitude,employee.location_longitude)
            # calculate distance between two point 
            dist        =   gd(user_location,emp_location).km

            # if dist is less than 6 km append list
            # if dist <= 5:
            #     user_list.append(employee.user_id)
            #     emp_fcm.append(employee.user_fcm_token)
            #     emplist[str(employee.user_id)] = list((str(employee.user_fcm_token),str(employee.device_type))) 

            api_key  =  'AIzaSyC2o6UvDF6qUUQM3KCwR6dwoV5qCfj8MGs'
            url      =  f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={job_instance.location_latitude},{job_instance.location_longitude}&destinations={employee.location_latitude},{employee.location_longitude}&key={api_key}"
            response =  requests.get(url)
            data     =  response.json()

            try:
                duration_seconds = data['rows'][0]['elements'][0]['duration']['value']
            except KeyError:
                duration_seconds =''


            # if dist is less than 6 km append list 
            if duration_seconds != '':
                if int(duration_seconds) <= 1260:
                    user_list.append(employee.user_id)
                    emp_fcm.append(employee.user_fcm_token)
                    emplist[str(employee.user_id)] = list((str(employee.user_fcm_token),str(employee.device_type))) 


    if len(user_list) == 0:
        client_fcm = job_instance.user.user_fcm_token
        noti_data={ }  
    
        data = { 
             'title'                      :     'Not Accepted',             
             'notificationScreenType'     :     'addjob',
             'message'                    :     'We are currently not available in your area. Coming soon',
             'job_id'                     :     str(job_id),  
             'job_type'                   :     job_instance.job_type
            }
        
        noti_data['fcm_token']  =   client_fcm 
        noti_data['device']     =   str(employee.device_type)
        noti_data['data']       =   data

            # sends push notification

        FCM.send_notification(noti_data)

        job_status      = JobsType.objects.get(status_id=5)
        update_record   = {
            "job_status" : job_status.status_id 
            }

        job_serializer = JobsSerializer(instance=job_instance,data=update_record,partial=True)
        if job_serializer.is_valid():
            job_serializer.save()

        return True
    
    
    emp_lis         =   ','.join(str(i) for i in user_list)
    alert_title     =    "new job added"
    alert_messages  =    "job generated"
    created_at      =     datetime.datetime.now()
    
    # Alert Table Save entry
    data            =   Alerts(alert_job=job_instance, alert_users=emp_lis,alert_title=alert_title,
                             alert_messages=alert_messages,
                            created_at=created_at) 
    data.save() 
    noti_data={ }  

    # pass dictionary data to send notification
    not_data = { 
             'title'                      :     'New job request',             
             'notificationScreenType'     :     'addjob',
             'message'                    :     message,
             'job_id'                     :     str(job_id),  
             'job_type'                   :     job_instance.job_type
            }
    job_status      = JobsType.objects.get(status_id=1)
    update_record   = {
        "job_status" : job_status.status_id 
        }
    
    job_serializer = JobsSerializer(instance=job_instance,data=update_record,partial=True)
    if job_serializer.is_valid():
        job_serializer.save()

    # SEND NOTIFICATIONS 
    
    for employee in employees:
        if employee.user_fcm_token!=None and employee.user_fcm_token!='':
            noti_data['data']       =   not_data
            noti_data['fcm_token']  =   employee.user_fcm_token 
            noti_data['device']     =   str(employee.device_type)
            # sends push notification
            FCM.send_notification(noti_data)
     
    return True







'''API for GET client job list'''
@api_view(['POST'])
def client_joblist(request):
    
    token       = request.headers['Authorization']
    user_token  = token.replace("Bearer",'')  
    check_user  = token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
                })
    
    # if token verified
    else:
        user_id         =   check_user['session_user']
       
        '''REQUIRED DATA FOR PAGE NUMBER'''
        page_no         =   int(request.data.get('page_no'))

        total_records   =   Jobs.objects.exclude(is_delete=1).filter(user=user_id).count()
        
        '''PAGE NUMBER STARTS WITH 0 AND ENDS WITH TOTAL PAGES-1'''
        limit           =   10
        offset          =   (page_no-1)*limit
        try:
            total_pages     =   math.ceil(total_records / limit)
        except:
            total_pages    =    0
        jobs_list       =   Jobs.objects.exclude(is_delete=1).filter(user=user_id)[offset:limit+offset]

        
        job_serializer  =   JobsSerializer(jobs_list,many=True).data

        removeElements(['is_delete','vehicle_license','location_latitude','location_longitude','user'],job_serializer) 

        for job in job_serializer:

            if job['job_pay_status'] == True:
                job['job_pay_status'] = "1"
            else:
                job['job_pay_status'] = "0"

            if job['job_status'] == 1:
                job['job_status'] = "active"

            elif job['job_status'] == 2:
                job['job_status'] = "accepted"

            elif job['job_status'] == 3:
                job['job_status'] = "completed"
            
            elif job['job_status'] == 4:
                job['job_status'] = "Not accepted"
            
            else:
                job['job_status'] = "cancelled"

            ''' print employee name==> job accepted by '''   

            if job['job_accepted_by'] != None:
                employee_record         =   Registration.objects.exclude(user_is_delete=1).get(user_id=int(job['job_accepted_by']))            
                job['job_accepted_by']  =   employee_record.user_first_name+ ' ' +employee_record.user_last_name
        

        # response data
        data = {
            "client_joblist"    :   job_serializer,
            "total_pages"       :   total_pages,
            "per_page_record"   :   10,
            "current_page"      :   page_no,            
            "total_records"     :   total_records
        }
        return JsonResponse({
                "success"     :   1,
                "message"     :   "joblist fetched",
                "data"        :    data
                })
    


'''API for GET Employee job list'''
@api_view(['POST'])
def employee_joblist(request):

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
        user_id         =   check_user['session_user']
        page_no         =   int(request.data.get('page_no'))

        '''
        ALL ACTIVE JOBS THIS EMPLOYEE HAS NOT ALREADY REJECTED/CANCELLED STAY IN THE
        LIST, EVEN IF THE PUSH NOTIFICATION WAS DISMISSED OR THE APP WAS CLOSED.
        '''
        available_ids   =   set()
        active_jobs     =   Jobs.objects.exclude(is_delete=1).filter(job_status_id=1)
        for job_record in active_jobs:
            if not has_attempted(job_record,user_id):
                available_ids.add(job_record.job_id)

        joblist_filter  =   Jobs.objects.exclude(is_delete=1).exclude(job_status_id=4).filter(
                                Q(job_accepted_by=user_id) | Q(job_id__in=available_ids)
                            ).order_by('-job_id')

        total_records   =   joblist_filter.count()

        '''JOB LIST PAGINATION CODE'''

        limit           =   10
        offset          =   (page_no-1)*limit    #multiply record each time
        total_pages     =   math.ceil(total_records / limit) #TOTAL NO OF PAGES

        jobs_list       =   list(joblist_filter[offset:limit+offset])

        job_serializer  = JobsSerializer(jobs_list,many=True).data

        '''FLAGS THE APP NEEDS TO DECIDE WHICH BUTTONS/SCREEN TO SHOW'''
        for job_record,job in zip(jobs_list,job_serializer):

            job['is_assigned']  =   1 if (job_record.job_accepted_by != None and int(job_record.job_accepted_by) == int(user_id)) else 0
            job['can_accept']   =   1 if (job_record.job_status_id == 1 and not has_attempted(job_record,user_id)) else 0
            job['was_notified'] =   1 if was_alerted(job_record,user_id) else 0

        '''Remove element from serlialized dict'''
        removeElements(['is_delete','vehicle_license','location_latitude','location_longitude','job_accepted_by'],job_serializer)

        for job in job_serializer:

            if job['job_pay_status'] == True:
                job['job_pay_status'] = "1"
            else:
                job['job_pay_status'] = "0"


            if job['job_status'] == 1:
                job['job_status'] = "active"

            elif job['job_status'] == 2:
                job['job_status'] = "accepted"

            elif job['job_status'] == 3:
                job['job_status'] = "completed"

            elif job['job_status'] == 5:
                job['job_status'] = "Not accepted"

            else:
                job['job_status'] = "cancelled"


            '''if job accepted print client name'''

            if job['user'] != None:
                employee_record         =   Registration.objects.exclude(user_is_delete=1).get(user_id=int(job['user']))
                job['client_name']      =   employee_record.user_first_name+ ' ' +employee_record.user_last_name



        removeElements(['user'],job_serializer)
        '''response data'''

        data = {
            "employee_joblist"  : job_serializer,
            "total_pages"       : total_pages,
            "per_page_record"   : 10,
            "current_page"      : page_no,
            "total_records"     : total_records

        }
        return JsonResponse({
                "success"     :   1,
                "message"     :   "joblist fetched",
                "data"        :    data
                })


'''
API TO RESTORE THE CURRENT JOB SESSION.

THE APP CALLS THIS ON LAUNCH/RESUME SO A JOB IS NEVER LOST WHEN THE EMPLOYEE
TAPS A NOTIFICATION AND THEN CLOSES THE APP, OR DISMISSES THE NOTIFICATION.

EMPLOYEE  ==>  THE JOB THEY ACCEPTED AND HAVE NOT FINISHED (job_state "in_progress"),
               OTHERWISE THE NEWEST ACTIVE JOB THEY WERE ALERTED ABOUT AND HAVE NOT
               ACCEPTED/REJECTED YET (job_state "pending").
CLIENT    ==>  THEIR OWN JOB THAT IS STILL WAITING FOR AN EMPLOYEE OR IN PROGRESS.
'''
@api_view(['POST','GET'])
def active_job(request):

    try:
        token   =   request.headers['Authorization']
    except KeyError:
        logger.error('active_job: Missing Authorization header')
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Missing Authorization header",
                })

    user_token  =   token.replace("Bearer",'')
    check_user  =   token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
                })

    # if token verified
    else:
        user_id     =   check_user['session_user']

        try:
            user_record =   Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
        except Registration.DoesNotExist:
            logger.warning('active_job: No registration found for user %s', user_id)
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Unauthorized User",
                    })

        job_record  =   None
        job_state   =   None

        '''EMPLOYEE'''
        if user_record.user_role_id == 1:

            # 1. JOB ALREADY ACCEPTED BY THIS EMPLOYEE AND NOT YET COMPLETED
            job_record  =   Jobs.objects.exclude(is_delete=1).filter(
                                job_status_id=2,job_accepted_by=str(user_id)
                            ).order_by('-job_id').first()

            if job_record != None:
                job_state = "in_progress"

            else:
                # 2. NEWEST ACTIVE JOB THIS EMPLOYEE WAS NOTIFIED ABOUT AND HAS NOT ACTED ON
                pending_jobs = Jobs.objects.exclude(is_delete=1).filter(job_status_id=1).order_by('-job_id')

                for pending in pending_jobs:
                    if has_attempted(pending,user_id):
                        continue
                    if not was_alerted(pending,user_id):
                        continue

                    job_record  =   pending
                    job_state   =   "pending"
                    break

        # CLIENT
        else:
            job_record  =   Jobs.objects.exclude(is_delete=1).filter(
                                user=user_id,job_status_id__in=[1,2]
                            ).order_by('-job_id').first()

            if job_record != None:
                job_state = "in_progress" if job_record.job_status_id == 2 else "pending"

        if job_record is None:
            return JsonResponse({
                    "success"     :   1,
                    "message"     :   "No active job",
                    "data"        :   {
                        "has_active_job"    :   0,
                        "active_job"        :   None
                        }
                    })

        job_payload =   build_job_payload(job_record)
        job_payload.pop('job_attempted_by',None)

        job_payload['job_state']    =   job_state
        job_payload['can_accept']   =   1 if (user_record.user_role_id == 1 and job_record.job_status_id == 1 and not has_attempted(job_record,user_id)) else 0

        '''SAME SCREEN TYPE THE PUSH NOTIFICATION CARRIES, SO THE APP REUSES ITS HANDLER'''
        if user_record.user_role_id == 1:
            job_payload['notificationScreenType'] = 'addjob' if job_state == "pending" else 'acceptjob'
        else:
            job_payload['notificationScreenType'] = 'acceptjob' if job_state == "in_progress" else 'addjob'

        '''CLIENT NAME FOR THE EMPLOYEE SCREEN'''
        try:
            client_record   =   Registration.objects.exclude(user_is_delete=1).get(user_id=job_record.user_id)
            job_payload['client_name']  =   client_record.user_first_name+ ' ' +client_record.user_last_name
        except Registration.DoesNotExist:
            logger.warning('active_job: Client %s missing for job %s', job_record.user_id, job_record.job_id)

        return JsonResponse({
                "success"     :   1,
                "message"     :   "Active job fetched",
                "data"        :   {
                    "has_active_job"    :   1,
                    "active_job"        :   job_payload
                    }
                })


import os
@api_view(['POST'])
def upload_images(request):

    token       = request.headers['Authorization']
    user_token  = token.replace("Bearer",'')  
    check_user  = token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
                })
    
    # if token verified
    else:
        job_id   =  request.data.get("job_id")
        img_type =  request.data.get("img_type")
        image_list  =  request.FILES.getlist('image')

        if job_id == '' or job_id == None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide a job id"
            })

        if img_type == '' or img_type == None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide a image type"
            })
        if image_list == '' or image_list == None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide a image type"
            })
        
        job_check = Jobs.objects.exclude(is_delete=1).filter(job_id=job_id).exists()
        if job_check ==False:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Job does not exist"
            })
        if img_type != "before" and img_type != "after":
             return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide a image type before or after"
            })
        for image in image_list: 
            try:
                im = Image.open(image)
                im.verify()
            except:
                im = None

            if im is None: 
                return JsonResponse({
                    "success"     :   0,
                    "message"     :   "please provide valid image",
                })

        job_rec  = Jobs.objects.exclude(is_delete=1).get(job_id=job_id)
        if img_type == 'before':
            img_type = 1
        else:
            img_type = 2

        img_data =      Images(
            job        = job_rec,
            
            img_type   = img_type,
            created_at = timezone.now(),
            is_delete  = 0
        )
        img_data.save()
        # img_id = img_data.img_id 

        for image in image_list:

        
            filename = os.path.basename(image.name)
            # ext     =   filename.split('.')[-1]
            # name    =   filename.split('.')[0]
            count   =   0
            name, ext = os.path.splitext(filename)
    
            if len(name) > 12:
                name = name[:12]
            
            # for i in range(0, len(filename)):  
            #     if(filename[i] != ' '):  
            #         count = count + 1

            #     if count >=12:
            #         name = str(filename)[0:12]

            time     =   (timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
            filename =   "%s%s.%s" % (name,str(time),ext)
            # original_string = 'Jonaten_bann2023-07-27 20:12:10.png'
            modified_string = filename.replace(' ', '_').replace(':', '') 
            file_path_name = os.path.join('attachments/',modified_string)
                # apirequest.png
            file = File(file            = image,
                        file_name       = image,
                        file_path       = "media/attachments",
                        file_system_name= file_path_name ,
                        file_img        = img_data
                        )
            file.save()
    
        return JsonResponse({
                "success"     :   1,
                "message"     :   "Images uploaded successfully"
            })

@api_view(['POST'])

def getuploaded_image(request):
    
    token       = request.headers['Authorization']
    user_token  = token.replace("Bearer",'')  
    check_user  = token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
                })
    
    # if token verified
    else:
        job_id   =  request.data.get("job_id")

        if job_id == '' or job_id == None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide a job id"
            })

        job_check = Jobs.objects.exclude(is_delete=1).filter(job_id=job_id).exists()
        if job_check ==False:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Job does not exist"
            })
        
        domain =  env('BASE_URL')
        images = Images.objects.exclude(is_delete=1).filter(job=int(job_id)).exists()
        if images == False:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Images does not exist"
            })
        
        img_id_list = Images.objects.exclude(is_delete=1).filter(job=job_id)

        imges_list = []
       
        for image in img_id_list:
            img_dict   = {}
            if image.img_type == 1:
                img_dict['type'] = "Before"
            else:

                img_dict['type'] = "After"
            
            files  = File.objects.exclude(is_delete=1).filter(file_img=image.img_id).exists()

            if files:
                files_list = File.objects.exclude(is_delete=1).filter(file_img=image.img_id)

                img_list   = []
                for file in files_list:

                    image = domain + file.file.url
                    img_list.append(image)
                    img_dict['images'] = img_list
                imges_list.append(img_dict)
        return JsonResponse({
            "success"     :   1,
            "message"     :   "Images get successfully",
            "data"        : imges_list
        })









