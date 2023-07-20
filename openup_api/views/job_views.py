# IMPORT CELERY
from openup import celery_app
 

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
from openup_app.models import Registration,JobsType,Jobs,Alerts,VehicleDetails,Payment,PaypalInfo

# Import Serializer
from openup_app.serializers import JobsSerializer

# Import pillow
from PIL import Image

# Import Q
from django.db.models import Q

# IMPORT SHARED TASK
from celery import shared_task

from .validation import check_number,check_text

import requests
 
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
              
                # "vehicle_details"       :   vehicle_details,
                # "vehicle_modification"  :   vehicle_modification,
                "vehicle_license"       :   license,
                "created_at"            :   created_at,
                "user"                  :   user_rec.user_id,
                "job_status"            :   job_id.status_id,
                "year"                  :   year,
                "model"                 :   model,
                "colour"                :   colour,
                "any_mod"               :   any_mod,
                "window_tint"           :   window_tint         
        }
        job_ser     =   JobsSerializer(data=job_details)

        # get serializer data
        if job_ser.is_valid():
            id = job_ser.save()
            '''
                JOB ALERT IS SHARED TASK FUNCTION RUN IN BACKGROUND @shardtask decorator required
            '''

            jobAlert.delay(id,current_location_lat,current_location_long)


            payment_type = user_rec.user_payment_type
            if payment_type == "stripe":
                # '''Payment code '''
                background_payment.delay(user_id,id)

            if payment_type=="paypal":
                # try: 
                #     check_job = Jobs.objects.exclude(is_delete=1).filter(user=user_rec.user_id).exists()
                # except:
                #     check_job = False
                # # if no job found means user is new
                # if check_job == False:

                data = {
                    "user"          :   user_id,
                    "job_id"        :   id,
                    "paypal_req_id" :   paypal_req_id,
                    
                }
                paypal_payment(data)
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

# @shared_task()
def paypal_payment(data):
        

        job_id           =   data['job_id']
        paypal_req_id   =   data['paypal_req_id']  # random text 
        login_user      =   data['user']
        paypal_data     =   PaypalInfo.objects.filter(paypal_user=login_user).values().first()

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
                    "amount": {
                        "currency_code": "USD",
                        "value": "100.00"
                    }
                }
            ],
            "payment_source": {
                "card": {
                    "vault_id":paypal_data['paypal_valut_id'] 
                            }          
                        }
                    }

        # # Send payment request
        url = 'https://api-m.sandbox.paypal.com/v2/checkout/orders'
        headers = {'Content-Type': 'application/json','PayPal-Request-Id': paypal_req_id, 'Authorization': 'Bearer ' +access_token}
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
         
        
        # payload_data = {
        #     "paypal_req_id" :   paypal_req_id,
        #     "payload"       :   payload,
        #     "access_token"  :   access_token,
        #     "url"           :   url,
        #     "job_id"        :   job_id,
        #     "paypal_valut_id":paypal_data['paypal_valut_id']
        #     }
        # SEND PAYLOAD TO BACKGROUND TO INITIATE PAYMENT

        # PaypalPayment.background_payments(payload_data)

        data = {
            "job_id" : job_id,
        }
        # # Update job after successfull payment.
        job_record = Jobs.objects.exclude(is_delete=1).get(job_id=int(data['job_id']))   

        
        update_payment_status = {
                "job_payment_id"    :      data['job_id'],
                "job_pay_status"    :      1 
                } 
        
        job_ser  = JobsSerializer(instance=job_record,data=update_payment_status,partial=True)
        if job_ser.is_valid():
            job_ser.save()
        return True

























'''
 JobAlert function calls whenever new job added by client

 latitude and longitude pass by client 

 SERVICE_JOB == >  ALERT TO ACTIVE EMP
 EMERGENCY_JOB ==> ALERT TO ACTIVE AND INACTIVE EMP

'''
@shared_task()
def jobAlert(job_id,latitude,longitude):
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
    '''IN EMPLOYEE DICT   KEY == > EMPLOYEE_ID  VALUE_LIST ==> [FCM,DEVICE TYPE]'''
    for employee in employees:
        if employee.user_fcm_token != "" or employee.user_fcm_token != None: 
            # user location
            user_location = (latitude,longitude)
            # employee location
            emp_location =  (employee.location_latitude,employee.location_longitude)
            # calculate distance between two point 
            dist        =   gd(user_location,emp_location).km

            # if dist is less than 6 km append list
            # if dist <= 6:
            user_list.append(employee.user_id)
            emp_fcm.append(employee.user_fcm_token)
            emplist[str(employee.user_id)] = list((str(employee.user_fcm_token),str(employee.device_type))) 
    
    # if len(user_list) == 0:
    #     for employees in employees:
    #         if employees.user_fcm_token == "" or employees.user_fcm_token == None:
    #             pass
    #         else:
    #             dist_list = []

    #             user_location       =   (latitude,longitude)
    #             emp_location        =   (employees.location_latitude,employees.location_longitude)
    #             # calculate distance between two point 
    #             dist                =   gd(user_location,emp_location).km

    #             # if dist is less than 6 km append list
    #             if dist <= 10:
    #                 user_list.append(employees.user_id)
    #                 emp_fcm.append(employees.user_fcm_token)
    #                 emplist[str(employees.user_fcm_token)] = list((str(employees.user_id),str(employees.device_type))) 

    emp_lis         =   ','.join(str(i) for i in user_list)
    alert_title     =    "new job added"
    alert_messages  =    "job generated"
    created_at      =     datetime.datetime.now()
    
    # Alert Table Save entry
    data            =   Alerts(alert_job=job_instance, alert_users=emp_lis,alert_title=alert_title,
                             alert_messages=alert_messages,
                            created_at=created_at) 
    # data.save() 

    # pass dictionary data to send notification
    data = { 
             'title'                      :     'New job request',             
             'notificationScreenType'     :     'addjob',
             'message'                    :     'Please acccept this asap',
             'job_id'                     :     str(job_id),  
             'job_type'                   :     job_instance.job_type
            }
             
    # SEND NOTIFICATIONS 
    noti_data={ }  
    
    for employee in employees:
        if employee.user_fcm_token!=None and employee.user_fcm_token!='':
            noti_data['data']       =   data
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
        
        # if block execute when job_accepted_by in job record is null
        if job_data.job_accepted_by != None:

            try:
                user_record = Registration.objects.exclude(user_is_delete=1).get(user_id=job_data.job_accepted_by)
            except:
                user_record = None
            
            if user_record != None:
                '''to get employee name '''            
                job_serializer['employee_name'] = user_record.user_first_name+' '+user_record.user_last_name

        job_serializer.pop('vehicle_license')

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
            'message'                           :   'Your job acepted',
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
        client_id       =       Jobs.objects.exclude(Q(job_status=1) and Q(job_status=3) and Q(job_status=4)).filter(job_id=job_id).values('user_id').first()['user_id']

    except:

        client_id   =   None

    
    client_record   =       Registration.objects.exclude(user_is_delete=1).get(user_id=client_id)
    
    # User information dictionary

    data = { 'title'                    :   'job completed',
            'notificationScreenType'    :   "completejob",
            'message'                   :   'Your job completed',
            'job_id'                    :   job_id
            }
        
    
    # SEND NOTIFICATIONS 

    noti_data={ }  
    noti_data['data'] = data
    noti_data['fcm_token']  =  (str(client_record.user_fcm_token))
    noti_data['device']     =   str(client_record.device_type)
    
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

    
        update_data = {
            "job_status" : 4
        }

        job_ser = JobsSerializer(instance=job_record,data=update_data,partial=True)

        if job_ser.is_valid():
            job_ser.save()
            return JsonResponse({
                    "success"     :   1,
                    "message"     :   "Your job is cancelled",
                    })
        else:
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "some error occured",
                    })

    
    


'''API for GET client job list'''
@api_view(['POST'])
def client_joblist(request):
    
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
        total_records   =   Jobs.objects.exclude(is_delete=1).filter(job_accepted_by=user_id).count()
        
        '''JOB LIST PAGINATION CODE'''
        
        limit           =   10
        offset          =   (page_no-1)*limit    #multiply record each time
        total_pages     =   math.ceil(total_records / limit) #TOTAL NO OF PAGES
      
        jobs_list       =   Jobs.objects.exclude(is_delete=1).filter(job_accepted_by=user_id)[offset:limit+offset]

        job_serializer  = JobsSerializer(jobs_list,many=True).data

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
            "current_page"      : page_no

        }
        return JsonResponse({
                "success"     :   1,
                "message"     :   "joblist fetched",
                "data"        :    data
                })
    



