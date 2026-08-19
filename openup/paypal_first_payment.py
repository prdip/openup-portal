from django.utils import timezone
import datetime,requests

# import serializer
from openup_app.serializers import PaymentFailedInfoSerializer, JobsSerializer
from openup_app.models import PaypalInfo,Jobs,PaymentFailedInfo,Registration
import json

# PAYPAL HOST HELPERS
from openup.paypal_api import paypal_url


# Reccuring payments using valut id of paypal customer




class First_PayPal_Payment:
    
    def background_payments(data):
        

        response = requests.post(paypal_url('/v2/checkout/orders/'), headers=data['headers'], json=data['payloads'])

        resp_data = json.loads(response.text)

        try:
            status = resp_data["status"]
        except:
            status = "Failed"
         
        try:
            if status != "COMPLETED":
                
                valut_id = resp_data['payment_source']["card"]["attributes"]["vault"]["id"]

                cust_id  = resp_data['payment_source']["card"]["attributes"]["vault"]["customer"]["id"]
                user = Registration.objects.get(user_id=data['user'])

                paypal_data = PaypalInfo(
                            paypal_user     =   user.user_id,
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

               
        except:
            # if payment failed then save the response in PaymentFailedInfo
            jobs =  Jobs.objects.get(job_id=data['job_id'])
           
 
            payment_ser = PaymentFailedInfo(
                user_id =data['user'],
                job_id  =jobs.job_id,
                payment_fail_type=resp_data['name'],
                payment_fail_response=resp_data,
                created_at=timezone.now()
            )
            payment_ser.save()