from django.shortcuts import render
#  Import Serializer

# Create your views here.
from rest_framework.decorators import api_view


# Import token verifivations

from openup_api.master.auth_views import token_verification


# Import json response
from django.http import JsonResponse



# API for force update 

@api_view(['POST'])
def force_update(request):

      # CHECK TOKEN VALUE
    user_token = request.data.get('user_token',None)

    check_user              =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })  
    else:


        version_list = {
        "anaroid_version"       :   1.3,
        "is_anaroid_update"     :   0,
        "ios_version"           :   1.3,
        "is_ios_update"         :   0

            
    }
   

        data = {
        
           "version_list"   :   version_list
            
        }    #0 ==> no        
    
    
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Force Update",
                "data"        :   data
        }) 