
# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse


# Import token verifications
from openup_api.views.auth_views import token_verification

# Import Models here
from openup_app.models import Settings

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
        

        # user_screen             =       request.data.get('user_screen')
        location                =       request.data.get('location',None)
        while_using             =       request.data.get('while_using',None)
        service_not             =       request.data.get('service_notification',None)
        location_notification   =       request.data.get('location_notification',None)
        service_feed_not        =       request.data.get('service_feed_not',None)
        # creates empty dictionary 
        user_id = check_user["session_user"]
        update_data = {}

        
        # if user_screen != None:
        #     update_data['user_screen'] = user_screen

        if location != None:
            update_data['location'] = location
        
        if while_using != None:
            update_data['while_using'] = while_using
        
        if service_not != None:
            update_data['service_notification'] = service_not
            
        if location_notification != None:
            update_data['location_notification'] = location_notification
        
        if service_feed_not != None:
            update_data['service_feed_not'] = service_feed_not

        for setting in update_data:
            try:
                setting_id       =   Settings.objects.exclude(is_delete=1).filter(Q(setting_user_id=int(user_id)) & Q(setting_name=str(setting)) ).values('setting_id').first()['setting_id']  
            except:
                pass
          
            try:
                setting_record   =   Settings.objects.exclude(is_delete=1).get(setting_id=setting_id)          
            except:
                pass
                
            data = {
                "setting_name"  :   str(setting),
                "setting_value" :   int(update_data[setting])
            }
            
          
            setting_ser     =   SettingsSerializer(instance=setting_record,data=data,partial=True)
            if setting_ser.is_valid():
                setting_ser.save()
            #     # pass

        return JsonResponse({
        
            "success"     :   1,
            "message"     :   "settings updated successfully",        
            })   
           


'''API for LOGIN USER SETTINGS'''
           

@api_view(['POST'])
def setting_details(request):

    user_token      =       request.data.get('user_token',None)
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })
    else:
        
        user    =  check_user['session_user']

        try:
                setting_record   =   Settings.objects.exclude(is_delete=1).filter(setting_user=int(user)).values('setting_name','setting_value')        
        except:
                pass
        
        setting_details = {}
        for seting in setting_record:
              
            if seting['setting_value'] == True:
                seting['setting_value'] = 1
       
            if seting['setting_value'] == False:
                seting['setting_value'] = 0

            setting_details[seting['setting_name']] =  seting['setting_value']


        data = {
            "setting_details":setting_details
        }
        return JsonResponse({
        
            "success"     :   1,
            "message"     :   "settings updated successfully",
            "data"        :     data
        
            })   




