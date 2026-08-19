import stripe,json
 
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
from openup_app.models import PaypalInfo, PaymentFailedInfo,SuccessPayments

# PAYPAL HOST HELPERS
from openup.paypal_api import paypal_url



# Reccuring payments using valut id of paypal customer




class PaypalPayment:
    
    def background_payments(data):
        
        # payload={
        #     "intent": "CAPTURE",
        #     "purchase_units": [
        #         {
        #             "amount": {
        #                 "currency_code": "USD",
        #                 "value": "100.00"
        #             }
        #         }
        #     ],
        #     "payment_source": {
        #         "card": {
        #             "vault_id":data['paypal_valut_id'] 
        #                     }          
        #                 }
        #             }

        # Send payment request
        url = paypal_url('/v2/checkout/orders')
        headers = {'Content-Type': 'application/json','PayPal-Request-Id':data['paypal_req_id'] , 'Authorization': 'Bearer ' +data['access_token']}
        response = requests.post(url, headers=headers, json=data["payload"])
        resp_data = json.loads(response.text)



    

        try:
            error = resp_data["name"]
        except:
            error = False

        if error == "UNPROCESSABLE_ENTITY" or error == "INVALID_REQUEST":
            paypal_data = PaymentFailedInfo(
                user_id=data["user_id"], job_id=data["job_id"], payment_fail_response=resp_data, created_at=timezone.now()
            )
            paypal_data.save()
            return True

        try:
            status = resp_data["status"]
        
        except:
            status = False
        
        if status == "PAYER_ACTION_REQUIRED":
            paypal_data = PaymentFailedInfo(
                user_id=data["user_id"], job_id=data["job_id"], payment_fail_response=resp_data, created_at=timezone.now()
            )
            paypal_data.save()
            return True

        # try:
        #     status = resp_data["status"]
        # except:
        #     status = "Failed"
         

        # if status != "Failed": 
        # # '''updated only on successfull payment'''    

        #     valut_id = resp_data["id"]
        #     cust_id  =  resp_data["customer"]["id"]
        #     paypal_data = PaypalInfo(
        #                 paypal_user     =   data['user'],
        #                 paypal_valut_id =   valut_id,
        #                 paypal_response =   resp_data,
        #                 paypal_cust_id  =   cust_id,
        #                 is_delete       =   0,
        #                 created_at      =    timezone.now()  
        #     )
        #     paypal_data.save()
            
        job_record = Jobs.objects.exclude(is_delete=1).get(job_id=int(data['job_id']))   
        update_payment_status = {
                "job_payment_id"    :      data['job_id'],
                "job_pay_status"    :      1 
                }   
            
        job_ser  = JobsSerializer(instance=job_record,data=update_payment_status,partial=True)
        if job_ser.is_valid():
            job_ser.save()
             
        
        '''
        source_type TELLS APART A VAULTED CARD ("paypal") FROM A VAULTED VENMO
        ACCOUNT ("venmo"). IT DEFAULTS TO "paypal" SO EXISTING CALLERS THAT DO NOT
        PASS IT KEEP WRITING THE SAME VALUE THEY ALWAYS DID - add_job READS THIS
        BACK TO REPLAY THE LAST PAYMENT METHOD ON EMERGENCY JOBS.
        '''
        pay_type = data.get("source_type") or "paypal"
        if pay_type == "card":
            pay_type = "paypal"

        pay_info = SuccessPayments(
        pay_user = data["user_id"],
        pay_job = data["job_id"],
        pay_type = pay_type,
        pay_response = resp_data,
        create_at = timezone.now())
        pay_info.save()
        return True
        
        # else:
        #     jobs =  Jobs.objects.get(job_id=data['job_id'])
           
 
        #     payment_ser = PaymentFailedInfo(
        #         user_id =data['user'],
        #         job_id  =jobs.job_id,
        #         payment_fail_type=resp_data['name'],
        #         payment_fail_response=resp_data,
        #         created_at=timezone.now()
        #     )
        #     payment_ser.save()
        #     return True 


