# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse

# Import token verifications
from openup_api.views.auth_views import token_verification

#  Import Serializer
from openup_app.serializers import RegisterSerializer,JobsSerializer

# Import Models here
from openup_app.models import Registration,Jobs

# Import Q
from django.db.models import Q
 

from geopy.distance import geodesic as gd


#  API for location update

@api_view(['POST'])

def update_location(request):
       # CHECK TOKEN VALUE
   
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')  
    check_user            =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        }) 
    
    else:
        # required data
        latitude     =    request.data.get('latitude',None)
        longitude    =    request.data.get('longitude',None)
        job_time     =    request.data.get('job_time',None)
        job_id       =    request.data.get('job_id',None)
        job_distance =    request.data.get('job_distance',None)
        # 
        # check for blank value
     
        if job_distance ==  None:
            return JsonResponse({
                            "success"        :       0,
                            "message"        :      "Please provide distance"
            })
        if job_id == None:
            return JsonResponse({
                            "success"        :       0,
                            "message"        :      "Please provide job_id"
            })

        if job_time == None:
            return JsonResponse({
                            "success"        :       0,
                            "message"        :      "Please provide time"
            })

        if latitude is None:
            return JsonResponse({
                            "success"        :       0,
                            "message"        :      "Please provide lattitude"
            })

        if longitude is None:
            return JsonResponse({
                            "success"        :       0,
                            "message"        :      "Please provide lattitude"
            })     
        
    
        user_id = check_user['session_user']
        
        # update data
        location_details = {
                    "location_latitude"   :     latitude,
                    "location_longitude"  :     longitude,
        }

        # #instance of  user recored
        user_rec    =       Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
        # user serializer
        user_ser    =       RegisterSerializer(instance=user_rec,data=location_details,partial=True)

         
        
        try: 
            job     = Jobs.objects.exclude(is_delete=1).get(job_id=job_id)
        except:
            job     = None

      

        update_data = {
            "job_time"      :       job_time,
            "job_distance"  :       job_distance
        }

        job_ser     =       JobsSerializer(instance=job, data=update_data, partial=True)

        if job_ser.is_valid():

            job_ser.save()
        

        if user_ser.is_valid():
            user_ser.save()

      
        return JsonResponse({
                            "success"        :       1,
                            "message"        :      "User location updated succesfully",
                            # "data"           :      data
                            
            })
                            




'''api for client '''

@api_view(['POST'])
def dist_calculation(request):

    token       = request.headers['Authorization']
    user_token  = token.replace("Bearer",'')  
    check_user            =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        }) 
    
    else:
        job_id       =    request.data.get('job_id',None)    
        if job_id==0:
                return JsonResponse({
                                "success"        :       1,
                                "message"        :      "User location updated succesfully"
                        })
        try:
            job_record          =   Jobs.objects.exclude(is_delete=1).get(job_id=job_id)
        except:
            job_record = None

        if job_record == None:
            return JsonResponse({
                                "success"        :       0,
                                "message"        :      "provide job id"
                        })
       


        time_req = job_record.job_time
        
       
        data =  {
               
                "time"           :       str(time_req),      
            }       
        return JsonResponse({
                            "success"        :       1,
                            "message"        :      "User location updated succesfully",
                            "data"           :      data
                            
            })
        





# API FOR 
@api_view(['POST'])
def service_available(request):
        # CHECK TOKEN VALUE
     
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')  
    check_user            =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        }) 
    
    else:
        # required data

        latitude     =       request.data.get('latitude',None)
        longitude    =       request.data.get('longitude',None)


        if latitude is None or longitude is None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "location not provi",
            })

        user_record     =       Registration.objects.exclude(Q(user_is_delete=1) and Q(user_role=2) and Q(user_status=0)).values('user_id','location_latitude','location_longitude')
        
        # user current location
        user_loc        =       (latitude,longitude)

        # list of services in km
        services_list   =       []

        for user in user_record:        
            # employee location
            emp_loc     =       (user['location_latitude'],user['location_longitude'])
            
            # Employee client distance
            dist        =       gd(user_loc,emp_loc).km

            # Services list between 5 km.
            if dist < 5:
                services_list.append(dist)

        if len(services_list) == 0:
            data = {
                
                "service_available" :   False
            }
        
        else:
            data = {
                "service_available" :   True
            }
        return JsonResponse({
                "success"     :   1,
                "message"     :   "location fetched",
                "data"        :     data
            })

      

# def dist(lat1, long1, lat2, long2):
#     """
# Replicating the same formula as mentioned in Wiki
#     """
#     # convert decimal degrees to radians 
#     lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])
#     # haversine formula 
#     dlon = long2 - long1 
#     dlat = lat2 - lat1 
#     a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
#     c = 2 * asin(sqrt(a)) 
#     # Radius of earth in kilometers is 6371
#     km = 6371* c
#     return km



@api_view(['POST'])

def employee_location(request):
       # CHECK TOKEN VALUE
   
    token       =   request.headers['Authorization']
    user_token  =   token.replace("Bearer",'')  
    check_user  =   token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        }) 
    
    else:
        # required data
        latitude     =    request.data.get('latitude',None)
        longitude    =    request.data.get('longitude',None)

        if latitude is None:
            return JsonResponse({
                            "success"        :       0,
                            "message"        :      "Please provide lattitude"
            })

        if longitude is None:
            return JsonResponse({
                            "success"        :       0,
                            "message"        :      "Please provide lattitude"
            })     
        
    
        user_id = check_user['session_user']
        
        # update data
        location_details = {
                    "location_latitude"   :     latitude,
                    "location_longitude"  :     longitude,
        }

        # #instance of  user recored
        user_rec    =       Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
        # user serializer
        user_ser    =       RegisterSerializer(instance=user_rec,data=location_details,partial=True)

        if user_ser.is_valid():
            user_ser.save()

            return JsonResponse({
                            "success"        :       1,
                            "message"        :      "User location updated succesfully"
            })
        else:
            return JsonResponse({
                            "success"        :       0,
                            "message"        :      "something went wrong"
            })
