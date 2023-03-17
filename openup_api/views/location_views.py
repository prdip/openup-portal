# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse,HttpResponse

# Import token verifications
from openup_api.views.auth_views import token_verification

#  Import Serializer
from openup_app.serializers import RegisterSerializer

# Import Models here
from openup_app.models import Registration

from math import radians, cos, sin, asin, sqrt
# Import Q
from django.db.models import Q


from geopy.distance import geodesic as gd


#  API for location update

@api_view(['POST'])

def update_location(request):
       # CHECK TOKEN VALUE
    user_token            =       request.data.get('user_token',None)
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

        # check for blank value
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

        #instance of  user recored
        user_rec    =       Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
        # user serializer
        user_ser    =       RegisterSerializer(instance=user_rec,data=location_details,partial=True)

        data = {

                "location_details":location_details
            }
        if user_ser.is_valid():
            user_ser.save()
            return JsonResponse({
                            "success"        :       1,
                            "message"        :      "User location updated succesfully",
                            "data"          :       data
            })




# API FOR 
@api_view(['POST'])

def service_available(request):
        # CHECK TOKEN VALUE
    user_token            =       request.data.get('user_token',None)
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

        user = (latitude,longitude)
        dist_val = { }
        for user in user_record:
            

            # d1 = dist(float(latitude),float(longitude),float(user['location_latitude']),float(user['location_longitude']))
            
            # dist_val[str(user['user_id'])] = str(d1)

            emp_loc = (user['location_latitude'],user['location_longitude'])
            dist = gd(user,emp_loc)

            dist_val[str(user['user_id'])] = str(dist)

            print(dist_val)
        data = {
            "service_available" :   True
        }
        return JsonResponse({
                "success"     :   0,
                "message"     :   "location fetched",
                "data"        :     data
            })

        # latitude         =       user_record.location_latitude
        # longitude        =       user_record.location_latitude


        # pass


def dist(lat1, long1, lat2, long2):
    """
Replicating the same formula as mentioned in Wiki
    """
    # convert decimal degrees to radians 
    lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])
    # haversine formula 
    dlon = long2 - long1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371* c
    return km
