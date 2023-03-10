
# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse


# Import token verifications
from openup_api.views.auth_views import token_verification

import datetime 

from datetime import datetime

# Import Models here
from openup_app.models import Registration,JobsType

# Import Serializer
from openup_app.serializers import JobsSerializer

# Import pillow
from PIL import Image




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
        vehicle_license         =   request.data.get('vehicle_license',None)
        created_at              =   datetime.now()

        # job type accepts only employee and emergency

        if job_type is None or job_type ==  ""or job_type != "service" or job_type != "emergency":
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
        
        if vehicle_license != None:

                try:
                    im = Image.open(vehicle_license)
                    im.verify()

                except:
                    im = None

                if im is None: 
                    return JsonResponse({
                        "success"     :   0,
                        "message"     :   "Please provide valid image",
                    })
        else:
            return JsonResponse({
                        "success"     :   0,
                        "message"     :   "Please provide licence image",
                    })
        # get user id from token
        user_id     =       check_user['session_user']
        # get instance of login user
        user_rec    =       Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
        job_id      =       JobsType.objects.first()
        job_details = {

                "job_type"              :   job_type,
                "location_latitude"     :   current_location_lat,
                "location_longitude"    :   current_location_long,
                "vehicle_details"       :   vehicle_details,
                "vehicle_modification"  :   vehicle_modification,
                "vehicle_license"       :   vehicle_license,
                "created_at"            :   created_at,
                "user"                  :   user_rec.user_id,
                "job_status"            :   job_id.status_id               
        }
        # get serializer data
        job_ser     =   JobsSerializer(data=job_details)

        if job_ser.is_valid():
            job_ser.save()      
            return JsonResponse({
                "status"    :   1,
                "message"   :   "Details Added successfully"
                })
        else:
            return JsonResponse({
                "status"    :   0,
                "message"   :   "Details Added successfully",
                "errors"    :   job_ser.errors
                })




