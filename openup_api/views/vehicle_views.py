
# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse


# Import token verifivations
from openup_api.views.auth_views import token_verification

#  Import  Pillow 
from PIL import Image

# Import Models here
from openup_app.models import Registration,VehicleDetails

# Import Serializer
from openup_app.serializers import VehicleSerializer

# Import datetime module
import datetime




# API to add new vehicle 

@api_view(['POST'])

def add_vehicle(request):
    #  Token Verification

    user_token      =       request.data.get('user_token',None)
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        }) 

    else:
        # Required 
        vehicle_id              =       request.data.get('vehicle_id',None)
        vehicle_license_img     =       request.data.get('vehicle_license_img',None)

        if vehicle_id == None:

            vehicle_details         =       request.data.get('vehicle_details',None)
            vehicle_modification    =       request.data.get('vehicle_modification',None)

            # check vehicle_details
            if vehicle_details is None or vehicle_details == "":
                return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Please Provide Vehicle details",
            }) 

            # check vehicle_modification data
            if vehicle_modification is None or vehicle_modification == "":
                return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Please Provide Vehicle mod",
            })
            # Check file upload is image or not
            if vehicle_license_img != None:
                try:
                    im = Image.open(vehicle_license_img)
                    im.verify()

                except:
                    im = None

                if im is None: 
                    return JsonResponse({
                        "success"     :   0,
                        "message"     :   "Please provide valid image",
                    })

            # get user id from token 
            user_id     =   check_user['session_user']

            # get user record through id
            user        =   Registration.objects.exclude(user_is_delete=1).get(user_id = user_id)
            created_at  =   datetime.datetime.now()
            
            # Vehicle data 
            vehicle_data = {
                "user"                  :   user.user_id,
                "vehicle_details"       :   vehicle_details,


                "vehicle_modification"  :   vehicle_modification,
                "created_at"            :   created_at
            }
            
            if vehicle_license_img != None:
                    vehicle_data["vehicle_license"]   =   vehicle_license_img

            vehicle_record  =  VehicleSerializer(data=vehicle_data)

            if vehicle_record.is_valid():
                vehicle_record.save()
                return JsonResponse({
                        "success"      :   1,
                        "message"      :   "Vehicle Information Stored Successfully",
                        
                })
        else:

            update_data = {
                "vehicle_license"   :   vehicle_license_img

            }

            vehicle_details         =       request.data.get('vehicle_details',None)
            vehicle_modification    =       request.data.get('vehicle_modification',None)
            if vehicle_details != None:
                 update_data["vehicle_details"] = vehicle_details

            if vehicle_modification != None:
                 update_data["vehicle_modification"] = vehicle_modification
                 

            vehicle_rec     =   VehicleDetails.objects.get(vehicle_id=vehicle_id)
            vehicle_ser     =   VehicleSerializer(instance=vehicle_rec,data=update_data,partial=True)

            if vehicle_ser.is_valid():
                vehicle_ser.save()
                return JsonResponse({
                    "success"     :   1,
                    "message"     :   "Vehicle Information updated Successfully",
                    

                })



# Edit api call 
@api_view(['POST'])
def vehicle_edit(request):

    #  Token Verification
    user_token      =       request.data.get('user_token',None)
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        }) 
    
    else:
        # Required data
        vehicle_id              =       request.data.get('vehicle_id',None)
        vehicle_license_img     =       request.data.get('vehicle_license_img',None)

        if vehicle_id == None or vehicle_id == "":
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide valid vehicle id",
            }) 
        # Check for image 
        if vehicle_license_img is None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide valid image",
            })
        
        try:
            im = Image.open(vehicle_license_img)
            im.verify()

        except:
            im = None

        if im is None: 
                return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Please provide valid image",
                })

        # update image data

        update_data = {
                    "vehicle_license"   :   vehicle_license_img
                }     

        vehicle_rec     =   VehicleDetails.objects.get(vehicle_id=vehicle_id)
        vehicle_data    =   VehicleSerializer(data=update_data,instance=vehicle_rec,partial=True)

        if vehicle_data.is_valid():
            vehicle_data.save()
            return JsonResponse({
                "success"     :   1,
                "message"     :   "Vehicle information updated",
            })



# remove data from list
def removeElements(items,lists):
    for dict in lists:
        for item in items:
            del(dict[item])  
    return lists





@api_view(['POST'])

def vehicle_details(request):

    #  Token Verification
    user_token      =       request.data.get('user_token',None)
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        }) 
    
    else:

        #  Get details using id
        vehicle_id = request.data.get('vehicle_id',None)
        
        try:
            vehicle_details =   VehicleDetails.objects.get(vehicle_id=vehicle_id)
            # vehicle_details =   VehicleDetails.objects.last()
        
        except:
            vehicle_details = None
        
        if vehicle_details is None or vehicle_id   ==  None:
             return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide Vehicle id",
            })
        vehicle_ser     =   VehicleSerializer(vehicle_details).data
        # Remove created at field from dict

        vehicle_ser.pop('created_at')
        vehicle_ser.pop('vehicle_license')

        # import socket
        domain = "192.168.1.2:8000"
        # ipaddress = socket.gethostbyname(domain)
        # dom = socket.gethostbyaddr(ipaddress)


        obj = vehicle_details.vehicle_license.url
        url = 'http://{domain}{path}'.format(domain=domain, path=obj)
        vehicle_ser['vehicle_license_url'] = url

        img_name = str(vehicle_details.vehicle_license)
        img_name=img_name.replace("licenses/"," ")
        vehicle_ser['vehicle_image_name'] =    img_name
        data = {
             "vehicle_details" : vehicle_ser

        } 
        return JsonResponse({
                    "success"     :   1,
                    "message"     :   "Vehicle details provided",
                    "data"        :    data
        }) 


