
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
        # if setting_id == None:
        #     # add operation
        #     # required data
        #     user_screen             =       request.data.get('user_screen',None)
        #     location                =       request.data.get('location',None)
        #     while_using             =       request.data.get('while_using',None)
        #     service_notification    =       request.data.get('service_notification',None)
        #     location_notification   =       request.data.get('location_notification',None)
        #     service_feed_not        =       request.data.get('service_feed_not',None)

        #     setting_dict ={
        #         "user_screen"       :user_screen,
        #         "location":location,
        #         "while_using":while_using,
        #         "service_notification":service_notification,
        #         "location_notification":location_notification,
        #         "service_feed_not":service_feed_not

        #     }
            
        #     # check data provided or not
        #     if user_screen is None or user_screen == "":
        #         return JsonResponse({
        #         "success"     :   0,
        #         "message"     :   "please provide user screen data",
        #         })
            
        #     # check location provided or not
        #     if location is None or location == "":
        #         return JsonResponse({
        #         "success"     :   0,
        #         "message"     :   "please provide location data",
        #         })
            
        #     # check only while using app data provided or not
        #     if while_using is None or while_using == "":
        #         return JsonResponse({
        #         "success"     :   0,
        #         "message"     :   "please provide user screen data",
        #         })
            
        #     # check service notification data
        #     if service_notification is None or service_notification == "":
        #         return JsonResponse({
        #         "success"     :   0,
        #         "message"     :   "please provide user screen data",
        #         })
        #     # check location notification data
        #     if location_notification is None or location_notification == "":
        #         return JsonResponse({
        #         "success"     :   0,
        #         "message"     :   "please provide user screen data",
        #         })
            
        #     # check service feedack notification 

        #     if service_feed_not is None or service_feed_not == "":
        #         return JsonResponse({
        #         "success"     :   0,
        #         "message"     :   "please provide user screen data",
        #         })
            
        #     user_id         =   check_user['session_user']
        #     user            =   Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)

        #     for setting in setting_dict:
        #         setting_data    =       {
                           
        #                     "setting_user"      :       user.user_id,
        #                     "setting_name"      :       setting,
        #                     "setting_value"     :       setting_dict[setting],
        #                     "created_at"        :       datetime.now()
        #                 }
               
        #         setting_ser     =       SettingsSerializer(data=setting_data)
        #         if setting_ser.is_valid():
        #             setting_ser.save()
        #     return JsonResponse({
        #         "success"     :   1,
        #         "message"     :   "settings saved successfully",
        #         })
                
        # else:
            # Edit operation

        user_screen             =       request.data.get('user_screen')
        location                =       request.data.get('location')
        while_using             =       request.data.get('while_using')
        service_notification    =       request.data.get('service_notification')
        location_notification   =       request.data.get('location_notification')
        service_feed_not        =       request.data.get('service_feed_not')
        # creates empty dictionary 
        user_id = check_user["session_user"]
        print("user id ",user_id)
        update_data = {}
        
        if user_screen is not None:
            update_data['user_screen'] = user_screen
        if location is not None:
            update_data['location'] = location
        if while_using is not None:
            update_data['only_while_using'] = while_using
        if service_notification is not None:
            update_data['service_notification'] = service_notification
            
        if location_notification is not None:
            update_data['location_notification'] = location_notification
        if service_feed_not is not None:
            update_data['service_feed_not'] = service_feed_not
        for setting in update_data:
            setting_id =   Settings.objects.exclude(is_delete=1).filter(Q(setting_user_id=user_id) & Q(setting_name=setting)).values("setting_id").first()["setting_id"]    
            setting_record   =   Settings.objects.exclude(is_delete=1).get(setting_id=setting_id)
            data = {
                "setting_name"  :   setting,
                "setting_value" :   int(update_data[setting])
            }
            print(data)
            print(setting_record)
            setting_ser     =   SettingsSerializer(instance=setting_record,data=data,partial=True)
            if setting_ser.is_valid():
                setting_ser.save()
        return JsonResponse({
            "success"     :   1,
            "message"     :   "settings updated successfully",
            })            
        
            # edit operation





# API for setting details

@api_view(['POST'])
def setting_details(request):

     #  Token Verification

    user_token      =       request.data.get('user_token',None)
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })
    else:

        # 0 == > False   1==>true
        setting_id  =   request.data.get('setting_id',None)

        if setting_id is  None:
            return JsonResponse({
                    "success"     :   0,
                    "message"     :   "Please provide setting id",
                    })
        
        setting_record  =   Settings.objects.exclude(is_delete=1).get(setting_id=setting_id)
        # setting_record  =   Settings.objects.exclude(is_delete=1).last()

        setting_ser     =   SettingsSerializer(setting_record).data

        for key in setting_ser:
            if setting_ser[key] == False:
                setting_ser[key] = 0
            if setting_ser[key] == True:
                setting_ser[key] = 1
        
        # remove items from dict

        setting_ser.pop('created_at')
        data    =   {
                "setting_details"   :   setting_ser
        }
        return JsonResponse({
                    "success"     :   1,
                    "message"     :   "setting fetched successfully",
                    "data"        :   data
                    })
    

    

# remove data from list
def removeElements(items,lists):
    for dict in lists:
        for item in items:
            del(dict[item])  
    return lists
