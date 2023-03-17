
from openup import celery_app
from celery import shared_task

from time import sleep
# Create your views here.
from rest_framework.decorators import api_view


import socket

# from openup.fcm import FCM

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


from django.db.models import Q


import requests
import json,time

# CODE TO ALERT PUSH NOTIFICATION

def send_push_notifications(fcm_token,noti_data):
    # print(fcm_token)
    # print(noti_data)

    for val in fcm_token:
        # print("key is", val)
        # print("token is", fcm_token[val][0]) 
        # print("device is", fcm_token[val][1])


    # return "send" 
        serverKey = '***REMOVED_FCM_KEY***' 
    
        seconds     = 60*60*24
        expireTime  = int(time.mktime(time.localtime()))+int(seconds)
        url = 'https://fcm.googleapis.com/fcm/send'

    #  true == 1 false ==0
        body = {
              "data"  :   noti_data,
                  "notification":{  
                      "title"             :   noti_data['title'],
                      "body"              :   noti_data['message'],
                      "sound"             :   "notification.wav",
                      "content_available" :   "true" 
                  }, 

                "to"  :    val,   

                "apns":{
                    "headers":{
                        "apns-expiration":expireTime
                    }
                },
                "android":{
                    "ttl":str(seconds)+"s"
                },
                "webpush":{
                    "headers":{
                        "TTL":str(seconds)
                    }
                }  
                        
            }
    

    # Device type 

    #     if(fcm_token[val][1] ==1): 
    #         body = {  
    #             "data"  :   dataDict['data'], 
    #             "to"    :   dataDict['fcm_token'], 
    #             "apns":{
    #                 "headers":{
    #                     "apns-expiration":expireTime
    #                 }
    #             },
    #             "android":{
    #                 "ttl":str(seconds)+"s"
    #             },
    #             "webpush":{
    #                 "headers":{
    #                     "TTL":str(seconds)
    #                 }
    #             }  
    #         }
         
        headers = {
            "Content-Type":"application/json",
            "Authorization": "key="+str(serverKey)+""
        } 
        
        response  = requests.post(url, data=json.dumps(body), headers=headers)
        result =  response.content 
        return result






    # def sendNotification(dataDict): 
        
    #     seconds     = 60*60*24
    #     expireTime  = int(time.mktime(time.localtime()))+int(seconds)

        
    #     serverKey   ='***REMOVED_FCM_KEY***'
        
    #     url = 'https://fcm.googleapis.com/fcm/send'
    #     body = {  
    #             "data"  :   dataDict['data'],
    #             "notification":{  
    #                 "title"             :   dataDict['title'],
    #                 "body"              :   dataDict['message'],
    #                 "sound"             :   "notification.wav",
    #                 "content_available" :   "true" 
    #             }, 
    #             "to":dataDict['fcm_token'],
                
    #             "apns":{
    #                 "headers":{
    #                     "apns-expiration":expireTime
    #                 }
    #             },
    #             "android":{
    #                 "ttl":str(seconds)+"s"
    #             },
    #             "webpush":{
    #                 "headers":{
    #                     "TTL":str(seconds)
    #                 }
    #             }  
                        
    #         }
    #     if(dataDict['device'] and dataDict['device']==1): 
    #         body = {  
    #             "data"  :   dataDict['data'], 
    #             "to"    :   dataDict['fcm_token'], 
    #             "apns":{
    #                 "headers":{
    #                     "apns-expiration":expireTime
    #                 }
    #             },
    #             "android":{
    #                 "ttl":str(seconds)+"s"
    #             },
    #             "webpush":{
    #                 "headers":{
    #                     "TTL":str(seconds)
    #                 }
    #             }  
    #         }
         
    #     headers = {
    #         "Content-Type":"application/json",
    #         "Authorization": "key="+str(serverKey)+""
    #     } 
        
    #     response  = requests.post(url, data=json.dumps(body), headers=headers)
    #     result =  response.content 
    #     return result



    
    



    # headers = {
    #     'Content-Type': 'application/json',
    #     'Authorization': 'key=' + serverToken,
    # } 
    # body = {
    #         "notification" :     str(noti_data),
    #         "to"           :     str(fcm_token),
    #         "priority"     :     'high',
    #         #   'data'     :     dataPayLoad,
    #     }
    # response = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body))
    
