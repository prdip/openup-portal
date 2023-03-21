# import datetime
import requests,json,time
import environ
env = environ.Env()
environ.Env.read_env()


class FCM: 
    def send_notification(dataDict): 
        
        serverKey   = '***REMOVED_FCM_KEY***'
        

        seconds     = 60*60*24
        if 'expiry' in dataDict and  dataDict['expiry']!=None:
            seconds = dataDict['expiry'] 
        expireTime  = int(time.mktime(time.localtime()))+int(seconds)

        
        url     =   'https://fcm.googleapis.com/fcm/send'
        body    =   {  
                "data"                  :   dataDict['data'],
                "notification":{  
                    "title"             :   dataDict['data']['title'],
                    "body"              :   dataDict['data']['message'],
                    # "sound"             :   "notification.wav",
                    "content_available" :   "true" 
                }, 
                "to":dataDict['fcm_token'],
                
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
        if dataDict['device'] and dataDict['device']=='1':

            print("Anaroid")
            body = {  
                "data"  :   dataDict['data'], 
                "to"    :   dataDict['fcm_token'],
                "notification":{  
                    "title"             :   dataDict['data']['title'],
                    "body"              :   dataDict['data']['message'],
                   
                    "content_available" :   "true" 
                }, 
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
            "Authorization": "key="+str(serverKey)+""
        } 
        # print(body)
        response    =   requests.post(url, data=json.dumps(body), headers=headers)
        result      =   response.content 
        print(result)
        return result
    


# def send_push_notifications(fcm_token,noti_data):

#     for val in fcm_token:

#         serverKey   =   '***REMOVED_FCM_KEY***' 
#         # serverKey   = str(settings.FCM_DJANGO_SETTINGS["FCM_SERVER_KEY"])
#         seconds     =   60*60*24
#         expireTime  =   int(time.mktime(time.localtime()))+int(seconds)

#         url = 'https://fcm.googleapis.com/fcm/send'

#     # #  true == 1 false ==0

#         if fcm_token[val][1] == "False":
#             body = {
#                   "data"  :   noti_data,
#                       "notification":{  
#                           "title"             :   noti_data['title'],
#                           "body"              :   noti_data['message'],
#                           "sound"             :   "notification.wav",
#                           "content_available" :   "true" 
#                       }, 

#                     "to"  :    fcm_token[val][0],   

#                     "apns":{
#                         "headers":{
#                             "apns-expiration":expireTime
#                         }
#                     },
#                     "android":{
#                         "ttl":str(seconds)+"s"
#                     },
#                     "webpush":{
#                         "headers":{
#                             "TTL":str(seconds)
#                         }
#                     }  

#                 }


#             # # Device type  anaroid

#         if fcm_token[val][1] == "True": 

#             body = {  
#                 "data"  :   noti_data, 
#                 "to"    :   fcm_token[val][0], 
#                 "apns":{
#                     "headers":{
#                         "apns-expiration":expireTime
#                     }
#                 },
#                 "android":{
#                     "ttl":str(seconds)+"s"
#                 },
#                 "webpush":{
#                     "headers":{
#                         "TTL":str(seconds)
#                     }
#                 }  
#             }
         
#         headers = {
#             "Content-Type":"application/json",
#             "Authorization": "key="+serverKey
#         } 

#         response  = requests.post(url, data=json.dumps(body), headers=headers)
#         result =  response.content
        
#         return result



   
    




# def send_notifications(fcm_token,noti_data): 
#     print(fcm_token)    

#     # fcm_list = []
#     for val in fcm_token:

#         print(val)
#         print("Device",fcm_token[val][1])
#         print("FCM token",fcm_token[val][0])

#         # fcm_list.append(fcm_token[val][0])

#         serverKey   =   '***REMOVED_FCM_KEY***' 

#         seconds     =   60*60*24

#         expireTime  =   int(time.mktime(time.localtime()))+int(seconds)
 
#         url = 'https://fcm.googleapis.com/fcm/send'
 
#         #  true == 1 false ==0

#         # if fcm_token[val][1] == "False":
#         #     body = {
#         #           "data"  :   noti_data,
#         #               "notification":{  
#         #                   "title"             :   noti_data['title'],
#         #                   "body"              :   noti_data['message'],
#         #                   "sound"             :   "notification.wav",
#         #                   "content_available" :   "true" 
#         #               }, 
  
#         #             "to"  :    fcm_token[val][0],   
 
#         #             "apns":{
#         #                 "headers":{
#         #                     "apns-expiration":expireTime
#         #                 }
#         #             },
#         #             "android":{
#         #                 "ttl":str(seconds)+"s"
#         #             },
#         #             "webpush":{
#         #                 "headers":{
#         #                     "TTL":str(seconds)
#         #                 }
#         #             }   
#         #         }

  
#         # # Device type  anaroid
 
#         if fcm_token[val][1] == "True": 
 
#              body = {  
#                  "data"  :   noti_data, 

#                  "to"    :   fcm_token[val][0],

#                  "apns":{
#                      "headers":{
#                          "apns-expiration":expireTime
#                      }
#                  },
#                  "android":{
#                      "ttl":str(seconds)+"s"
#                  },
#                  "webpush":{
#                      "headers":{
#                          "TTL":str(seconds)
#                      }
#                  }  
#              }
          
#         headers = {
#             "Content-Type":"application/json",
#             "Authorization": "key="+serverKey
#         } 

#         response =    requests.post(url, data=json.dumps(body), headers=headers)
#         result =  response.content
#         return result
