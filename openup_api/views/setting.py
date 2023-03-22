
# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse


# Import token verifications
from openup_api.views.auth_views import token_verification

import datetime 

from datetime import datetime

# Import Models here
from openup_app.models import Settings,Registration

# Import Serializer
from openup_app.serializers import SettingsSerializer

from django.db.models import Q

# API for Add and update settings

@api_view(['POST'])


def add_settings(request):
    #  Token Verification
    user_token      =       request.data.get('user_token',None)
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })
    else:

        # setting_name  =   request.data.get('setting_name',None)
        

        user_screen             =       request.data.get('user_screen')
        location                =       request.data.get('location')
        while_using             =       request.data.get('while_using')
        service_notification    =       request.data.get('service_notification')
        location_notification   =       request.data.get('location_notification')
        service_feed_not        =       request.data.get('service_feed_not')
        # creates empty dictionary 
        user_id = check_user["session_user"]
        update_data = {}
        
        if user_screen != None:
            update_data['user_screen'] = user_screen

        if location != None:
            update_data['location'] = location
        
        if while_using != None:
            update_data['only_while_using'] = while_using
        
        if service_notification != None:
            update_data['service_notification'] = service_notification
            
        if location_notification != None:
            update_data['location_notification'] = location_notification
        
        if service_feed_not != None:
            update_data['service_feed_not'] = service_feed_not
        
        for setting in update_data:

            setting_id       =   Settings.objects.exclude(is_delete=1).filter(Q(setting_user_id=user_id) & Q(setting_name=setting)).values("setting_id").first()["setting_id"]    
            setting_record   =   Settings.objects.exclude(is_delete=1).get(setting_id=setting_id)
            data = {
                "setting_name"  :   setting,
                "setting_value" :   int(update_data[setting])
            }
            
            setting_ser     =   SettingsSerializer(instance=setting_record,data=data,partial=True)
            if setting_ser.is_valid():
                setting_ser.save()
        return JsonResponse({
            "success"     :   1,
            "message"     :   "settings updated successfully",
            })            
        
           
