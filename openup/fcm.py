# import datetime
import requests,json,time,os
import environ
env = environ.Env()
environ.Env.read_env()

FIREBASE_CRED_PATH = os.path.join(os.path.dirname(__file__), 'firebase-credentials.json')
from openup_app.models import Registration
from datetime import datetime, timezone
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleRequest
from django.utils.dateparse import parse_datetime

class FCM: 

    

    def send_notification(dataDict):
        
        seconds     =        60*60*24
        # serverKey   =       env('FCM_SERVER_KEY11')
        serverKey  =    FCM.access_token_get_or_update()

        if 'expiry' in dataDict and  dataDict['expiry']!=None:
            seconds = dataDict['expiry'] 
        expireTime  = int(time.mktime(time.localtime()))+int(seconds)

        
        # url     =   'https://fcm.googleapis.com/fcm/send'
        url = "https://fcm.googleapis.com/v1/projects/openup-2892b/messages:send"
        # body    = {
             
        #         "data"                  :   dataDict['data'],
        #         "notification":{  
        #             "title"             :   dataDict['data']['title'],
        #             "body"              :   dataDict['data']['message'],
        #             "sound"             :   "notification.wav",
        #             "content_available" :   "true" 
        #         }, 
        #         "token":dataDict['fcm_token'],
                
        #         "apns":{
        #             "headers":{
        #                 "apns-expiration":expireTime
        #             }
        #         },
        #         "android":{
        #             "ttl":str(seconds)+"s"
        #         },
        #         "webpush":{
        #             "headers":{
        #                 "TTL":str(seconds)
        #             }
        #         }  
                        
            
        # }

        body = {
            
        "message": {
            "data"                  :   dataDict['data'],
            "token": dataDict['fcm_token'],   
            "notification": {
                "title":  dataDict['data']['title'],
                "body":   dataDict['data']['title']
            }
        }
     

        }

        if dataDict['device'] and dataDict['device']=='1':

            # body = {
                 
            #         "data"  :   dataDict['data'], 
            #         "token"    :   dataDict['fcm_token'],
            #         "notification":{  
            #             "title"             :   dataDict['data']['title'],
            #             "body"              :   dataDict['data']['message'],
            #             "sound"             :   "notification.wav",
            #             "content_available" :   "true" 
            #         }, 
            #         "apns":{
            #             "headers":{
            #                 "apns-expiration":expireTime
            #             }
            #         },
            #         "android":{
            #             "ttl":str(seconds)+"s"
            #         },
            #         "webpush":{
            #             "headers":{
            #                 "TTL":str(seconds)
            #             }
            #         }  
                
            # }
            body = {
            
                "message": {
                    "data"                  :   dataDict['data'],
                    "token": dataDict['fcm_token'],   
                    "notification": {
                        "title":  dataDict['data']['title'],
                        "body":   dataDict['data']['title']
                    }
                }
            }
        headers = {
            'Content-Type': 'application/json; UTF-8',
            "Authorization": "Bearer "+str(serverKey)+""
        }
        try: 
            response    =   requests.post(url, data=json.dumps(body), headers=headers)
            result      =   response.content 

        except Exception as e:
            pass
        return result
    

    def access_token_get_or_update():
        user = Registration.objects.get(user_id=1)
        expiry_datetime = user.update_at
        if user.user_fcm_token == '' or user.user_fcm_token == None:
            # create token and add
            if isinstance(expiry_datetime, str):
                expiry_datetime = parse_datetime(expiry_datetime)
        
            if expiry_datetime is None or expiry_datetime < datetime.now(timezone.utc):
                access           = FCM.get_access_token()
                new_access_token = access['token']
                expiry           = access['expiry'] 

                expiry_str          = expiry.strftime('%Y-%m-%dT%H:%M:%S.%f%z')

                update_dict = {
                    'user_fcm_token': new_access_token,
                    'update_at': expiry_str
                }
                user.update(**update_dict)
                return new_access_token
            else:
                return user.user_fcm_token

        else:


            access           = FCM.get_access_token()
            new_access_token = access['token']
            expiry           = access['expiry']

            expiry_str          = expiry.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
            # user.user_fcm_token = new_access_token
            # user.update_at      = expiry_str
            # user.save()

            update_dict = {
                'user_fcm_token': new_access_token,
                'update_at': expiry_str
            }
            user.update(**update_dict)
            return new_access_token 


    def get_access_token():
        """Retrieve a valid access token that can be used to authorize requests.

        :return: Access token.
        """
        credentials = service_account.Credentials.from_service_account_file(
            FIREBASE_CRED_PATH,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

        # Refresh the credentials
        request = GoogleRequest()
        credentials.refresh(request)
        return credentials.__dict__