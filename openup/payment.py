import stripe
 
# import Json Response
from django.http.response import JsonResponse

# Import Models here
from openup_app.models import  Jobs,VehicleDetails

# Import Serializer
from openup_app.serializers import JobsSerializer

# import datetime
import datetime

# import serializer
from openup_app.serializers import PaymentFailedInfoSerializer

'''background payment 
required data ==> amount, currency, customer_id, payment_method_id 

'''

class Payments:
    
    def background_payments(data): 
       
        try:           
            payment_data    =  stripe.PaymentIntent.create(
                 
                amount          =   data['amount'],
                currency        =   data['currency'],
                customer        =   data['customer'],  
                payment_method  =   data['payment_method_id'],   
                metadata        =   data['metadata'],                
                off_session     =   True,
                confirm         =   True,
            ) 
           
        except stripe.error.CardError as e:
            error           = e.error      
            payment_details = {
                "user_id"               :   data['user_id'],
                "job_id"                :   data['job_id'],
                "payment_fail_type"     :   error['type'] ,
                "payment_fail_code"     :   error['code'],
                "payment_fail_message"  :   error['message'],
                "created_at"            :   datetime.datetime.now(),
            }
            payment_ser =   PaymentFailedInfoSerializer(data=payment_details)
            if payment_ser.is_valid():
                payment_ser.save()
                return True   
           
            
        except stripe.error.InvalidRequestError as e:
            error           = e.error      
            payment_details = {
                "user_id"               :   data['user_id'],
                "job_id"                :   data['job_id'],
                "payment_fail_type"     :   error['type'] ,
                "payment_fail_code"     :   error['code'],
                "payment_fail_message"  :   error['message'],
                "created_at"            :   datetime.datetime.now(),
            }

            payment_ser     =   PaymentFailedInfoSerializer(data=payment_details)
            if payment_ser.is_valid():
                payment_ser.save()
                return True   
         
            
        except Exception as e:
            error           = e.error      
            payment_details = {
                "user_id"               :   data['user_id'],
                "job_id"                :   data['job_id'],
                "payment_fail_type"     :   error['type'] ,
                "payment_fail_code"     :   error['code'],
                "payment_fail_message"  :   error['message'],
                "created_at"            :   datetime.datetime.now(),
            }
            payment_ser =   PaymentFailedInfoSerializer(data=payment_details)
            if payment_ser.is_valid():
                payment_ser.save()
                return True   

            
        '''updated only on successfull payment'''    



        job_record = Jobs.objects.exclude(is_delete=1).get(job_id=int(data['job_id']))  


        update_payment_status = {
                "job_payment_id"    :      payment_data['id'],
                "job_pay_status"    :      1 
                }   
        
        job_ser  = JobsSerializer(instance=job_record,data=update_payment_status,partial=True)
        if job_ser.is_valid():
            job_ser.save()
            return True

