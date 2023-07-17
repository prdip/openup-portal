import stripe
 
# import Json Response
from django.http.response import JsonResponse

# Import Models here
from openup_app.models import  Jobs 

# Import Serializer
from openup_app.serializers import JobsSerializer

from django.utils import timezone


# import datetime
import datetime,requests

# import serializer
from openup_app.serializers import PaymentFailedInfoSerializer
from openup_app.models import PaypalInfo, PaymentFailedInfo



# Reccuring payments using valut id of paypal customer




class Payments:
    
    def background_payments(data):
        
        payload={
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": "100.00"
                    }
                }
            ],
            "payment_source": {
                "card": {
                    "vault_id":data['paypal_valut_id'] 
                            }          
                        }
                    }

        # Send payment request
        url = 'https://api-m.sandbox.paypal.com/v2/checkout/orders'
        headers = {'Content-Type': 'application/json','PayPal-Request-Id':data['paypal_valut_id'] , 'Authorization': 'Bearer ' +data['access_token']}
        response = requests.post(url, headers=headers, json=payload)
        resp_data = response.json()



        try:
            status = resp_data["status"]
        except:
            status = "Failed"
         

        if status != "Failed": 
        # '''updated only on successfull payment'''    

            valut_id = resp_data['payment_source']["card"]["attributes"]["vault"]["id"]

            cust_id  = resp_data['payment_source']["card"]["attributes"]["vault"]["customer"]["id"]

            paypal_data = PaypalInfo(
                        paypal_user     =   data['user'],
                        paypal_valut_id =   valut_id,
                        paypal_response =   resp_data,
                        paypal_cust_id  =   cust_id,
                        is_delete       =   0,
                        created_at      =    timezone.now()  
            )
            paypal_data.save()
            
            job_record = Jobs.objects.exclude(is_delete=1).get(job_id=int(data['job_id']))   
            update_payment_status = {
                    "job_payment_id"    :      data['job_id'],
                    "job_pay_status"    :      1 
                    }   
            
            job_ser  = JobsSerializer(instance=job_record,data=update_payment_status,partial=True)
            if job_ser.is_valid():
                job_ser.save()
            return True 
        
        else:
            jobs =  Jobs.objects.get(job_id=data['job_id'])
           
 
            payment_ser = PaymentFailedInfo(
                user_id =data['user'],
                job_id  =jobs.job_id,
                payment_fail_type=resp_data['name'],
                payment_fail_response=resp_data,
                created_at=timezone.now()
            )
            payment_ser.save()


