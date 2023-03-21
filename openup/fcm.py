# import datetime
from datetime import datetime,timedelta,timezone
import requests,json,time


from openup import settings


def send_push_notifications(fcm_token,noti_data):

   
    for val in fcm_token:
        print("key is", val)
        print("token is", fcm_token[val][0]) 
        print("device is", type('fcm_token[val][1]'))
    
    

        serverKey   =   '***REMOVED_FCM_KEY***' 
        # serverKey   = str(settings.FCM_DJANGO_SETTINGS["FCM_SERVER_KEY"])
        seconds     =   60*60*24
        expireTime  =   int(time.mktime(time.localtime()))+int(seconds)

        print(expireTime)
        url = 'https://fcm.googleapis.com/fcm/send'

    # #  true == 1 false ==0

        # if fcm_token[val][1] == "True":
        #     body = {
        #           "data"  :   noti_data,
        #               "notification":{  
        #                   "title"             :   noti_data['title'],
        #                   "body"              :   noti_data['message'],
        #                   "sound"             :   "notification.wav",
        #                   "content_available" :   "true" 
        #               }, 

        #             "to"  :    fcm_token[val][0],   

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


    # # Device type  anaroid

        if fcm_token[val][1] == "True": 

            body = {  
                "data"  :   noti_data, 
                "to"    :   fcm_token[val][0], 
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
         
        headers = {
            "Content-Type":"application/json",
            "Authorization": "key="+serverKey
        } 

        print("header",headers)

        print("Body",body)
        
        response  = requests.post(url, data=json.dumps(body), headers=headers)
        result =  response.content
        print("result is",result)
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
    
