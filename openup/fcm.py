# import datetime
import requests,json,time
import environ
env = environ.Env()
environ.Env.read_env()




class FCM: 
    def send_notification(dataDict): 
        
        serverKey   =       '***REMOVED_FCM_KEY***'
        seconds     =        60*60*24

        
        if 'expiry' in dataDict and  dataDict['expiry']!=None:
            seconds = dataDict['expiry'] 
        expireTime  = int(time.mktime(time.localtime()))+int(seconds)

        
        url     =   'https://fcm.googleapis.com/fcm/send'
        body    =   {  
                "data"                  :   dataDict['data'],
                "notification":{  
                    "title"             :   dataDict['data']['title'],
                    "body"              :   dataDict['data']['message'],
                    "sound"             :   "notification.wav",
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

            body = {    
                "data"  :   dataDict['data'], 
                "to"    :   dataDict['fcm_token'],
                "notification":{  
                    "title"             :   dataDict['data']['title'],
                    "body"              :   dataDict['data']['message'],
                    "sound"             :   "notification.wav",
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
        
        print(body)
        headers = {
            "Content-Type":"application/json",
            "Authorization": "key="+str(serverKey)+""
        } 
        response    =   requests.post(url, data=json.dumps(body), headers=headers)
        result      =   response.content 
        print(result)
        return result
    

