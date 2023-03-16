
# Create your views here.
from rest_framework.decorators import api_view


import socket

from openup.fcm import FCM

# import Json Response
from django.http.response import JsonResponse


# Import token verifications
from openup_api.views.auth_views import token_verification

# import datetime
import datetime

# import datetime
from datetime import datetime,timedelta,timezone

# Import Models here
from openup_app.models import Registration,JobsType,Jobs,Alerts,VehicleDetails

# Import Serializer
from openup_app.serializers import JobsSerializer

# Import pillow
from PIL import Image

# Import Q
from django.db.models import Q


# ADD NEW JOB 
@api_view(['POST'])

def add_job(request):

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
        job_type                =   request.data.get('job_type',None)
        current_location_lat    =   request.data.get('latitude',None)
        current_location_long   =   request.data.get('longitude',None)
        vehicle_details         =   request.data.get('vehicle_details',None)
        vehicle_modification    =   request.data.get('vehicle_modification',None)
        license         =   request.data.get('vehicle_license',None)
        created_at              =   datetime.now()
        licence_name            =   request.data.get('licence_name',None)
        vehicle_id              =   request.data.get('vehicle_id',None)

        print(vehicle_id)
        # job type accepts only employee and emergency

        if job_type is None or job_type == "" or (job_type != "service" and job_type != "emergency"):
            return JsonResponse({
                    "status"    :   0,
                    "message"   :   "please provide job type"
                    })
        
        if current_location_lat is None or current_location_lat ==  "":
            return JsonResponse({
                    "status"    :   0,
                    "message"   :   "please provide current location "
                    })
        
        if current_location_long is None or current_location_long == "":
            return JsonResponse({
                    "status"    :   0,
                    "message"   :   "please provide current location "
                    })

        if vehicle_details is None or vehicle_details == "":
            return JsonResponse({
                    "status"    :   0,
                    "message"   :   "please provide current location "
                    })
        
        if vehicle_modification is None or vehicle_modification == "":
            return JsonResponse({
                    "status"    :   0,
                    "message"   :   "please provide current location "
                    })
        
        user_id     =       check_user['session_user']

        if vehicle_id == None and license ==  None:
            license = None
        
        
        else:


            if license is None and vehicle_id != None:
                
                print(license is None and vehicle_id != None)
                try:
                    veh_rec             =   VehicleDetails.objects.get(vehicle_id=vehicle_id)
                
                except:
                   veh_rec = None

                if veh_rec is not None:
                    license = veh_rec.vehicle_license
               

            elif license != None and vehicle_id == None:
                try:
                    veh_rec             =   VehicleDetails.objects.get(vehicle_id=vehicle_id)
                
                except:
                   veh_rec = None

               
                if veh_rec != None:
                    license = veh_rec.vehicle_license
               

                print("No license but veh image ",license)
                           
            else:
                try:
                        im = Image.open(license)

                except:
                        im = None

                if im is None: 
                    return JsonResponse({
                        "success"     :   0,
                        "message"     :   "Please provide valid image",
                    })
           
        # get user id from token
        
        # get instance of login user
        user_rec    =       Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
        job_id      =       JobsType.objects.first()
        job_details = {

                "job_type"              :   job_type,
                "location_latitude"     :   current_location_lat,
                "location_longitude"    :   current_location_long,
                "vehicle_details"       :   vehicle_details,
                "vehicle_modification"  :   vehicle_modification,
                "vehicle_license"       :   license,
                "created_at"            :   created_at,
                "user"                  :   user_rec.user_id,
                "job_status"            :   job_id.status_id               
        }
        # get serializer data
        job_ser     =   JobsSerializer(data=job_details)

        if job_ser.is_valid():

            id = job_ser.save()
            # id = 30
            # jobAlert(id)

            # time                =       datetime.now()
            # print("Thread end",time)       
             
            return JsonResponse({
                "status"    :   1,
                "message"   :   "Details Added successfully",
                })
       
        





# remove data from list
def removeElements(items,lists):
    for dict in lists:
        for item in items:
            del(dict[item])  
    return lists

from openup import celery_app
from celery import shared_task
@shared_task
# job alert to nearest employees
def jobAlert(job_id):
    # Fetch Employee List
    employees =  Registration.objects.exclude(Q(user_is_delete=1) or Q(user_role_id=2) ).filter(user_role=1)

    # get employee list
    user_list = []
    emp_fcm   = []
    
    for employees in employees:
        if employees.user_fcm_token == "" or employees.user_fcm_token is None:
            pass
        else:
            user_list.append(employees.user_id)
            emp_fcm.append(employees.user_fcm_token)

    emp_list        =   ','.join(str(i) for i in user_list)
    job_id          =    Jobs.objects.exclude(is_delete=1).get(job_id=job_id)
    alert_title     =    "new job added"
    alert_messages  =    "job generated"
    created_at      =     datetime.now()
    
    # Alert Table Save entry
    data            = Alerts(alert_job=job_id, alert_users=emp_list,alert_title=alert_title,
                             alert_messages=alert_messages,
                            created_at=created_at)
    
    data.save() 

    # send alert to employees
    # SEND NOTIFICATIONS 
    noti_data={
        'title'     :   'New job request',
        'message'   :   'Please acccept this asap',
        'job_id'    :   job_id, 
    }
    # import datetime
    for emp in emp_fcm: 
        print("Notification send",datetime.now())
        FCM.send_push_notifications(emp,noti_data)

    return True
    
    





@api_view(['POST'])


def job_list(request):
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
        job_list    =   Jobs.objects.exclude(Q(is_delete=1)and (Q(job_status=2)or Q(job_status=3))).all()
        job_ser     =   JobsSerializer(job_list,many=True).data
        # remove data from list
        removeElements(['created_at','is_delete'],job_ser) 

        domain = "192.168.1.5:8000"
        
        for data in job_ser:
            # get url of image
            obj = data['vehicle_license']
            url = 'http://{domain}{path}'.format(domain=domain, path=obj)
            data['vehicle_license'] = url

            if data['job_status'] == 1:
                data['job_status'] = "active"

            if data['job_status'] == 2:
                data['job_status'] = "accepted"

            if data['job_status'] == 3:
                data['job_status']="completed"
            
        data    =   {
            "job_list"  :   job_ser
            }
        return JsonResponse({
                "status"    :   1,
                "message"   :   "job list fetched successfully",
                "data"      :   data
                })



# Get detail of job 

@api_view(['POST'])
def job_details(request):
    #  Token Verification
    user_token      =       request.data.get('user_token',None)
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
        job_data        =   Jobs.objects.exclude(is_delete=1).get(job_id=job_id)
        # send instance to serializer 
        job_serializer  =   JobsSerializer(job_data).data
        
        # remove field from dict
        job_serializer.pop('created_at')        
        job_serializer.pop('is_delete')

        # create image url 
        # domain  = "192.168.1.5:8000"
        
        hostname = socket.gethostname()
        name = socket.gethostbyname(hostname)
        domain = name+":8000"

        # s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        # s.bind(('', 0))
        # owners_port = int(s.getsockname()[1])
        obj     = job_serializer['vehicle_license']
        url     = 'http://{domain}{path}'.format(domain=domain, path=obj)


        job_serializer['vehicle_license_url'] = url

        if job_serializer['job_status'] == 1:
            job_serializer['job_status'] = "active"
        
        if job_serializer['job_status'] == 2:
            job_serializer['job_status'] = "accepted"
        
        if job_serializer['job_status'] == "3":
            job_serializer['job_status']="completed"

        job_serializer.pop('vehicle_license')

        data = {
            "job_details":job_serializer
        }
        return JsonResponse({
                    "success"     :   1,
                    "message"     :   "Job Details fetched",
                    "data"        :     data
            })
    


@api_view(['POST'])

def remove_job(request):
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
        job_id      =       request.data.get('job_id',None)

        # check if jon id is blank
        if job_id is None or job_id == "":
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Please provide job id",
            })
        
        update_data     =   {
            "is_delete"     :       1
        }
        
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




# accept job api

@api_view(['POST'])


def accept_job(request):
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

        
        data = {
            "job_status"     :   2,
            "job_accepted_by":  user_record.user_id
        }   
        job_serializer= JobsSerializer(instance=job_record,data=data,partial=True)

        user_data = {
            "first_name"            :       user_record.user_first_name,
            "middle_name"           :       user_record.user_middle_name,
            "last_name"             :       user_record.user_last_name,
            "email"                 :       user_record.user_email,
            "mobile_number"         :       user_record.user_phone_number,
            "location_latitude"     :       user_record.location_latitude,
            "location_longitude"    :       user_record.location_longitude

        }
        data = {
            "employee" :   user_data
        }
        if job_serializer.is_valid():
            job_serializer.save(**data)

            return JsonResponse({
                            "success"     :   1,
                            "message"     :   "job accepted",
                            "data"        :     data
                    })
        
        else:

            return JsonResponse({
                            "success"     :   0,
                            "message"     :   "some error occured",
                    })




@api_view(['POST'])
def reject_job(request):
    pass