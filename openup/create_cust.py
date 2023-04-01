

#  Import Serializer
from openup_app.serializers import RegisterSerializer

# Import Models here
from openup_app.models import Registration 

# import stripe
import stripe

# Import Queryset
from django.db.models import Q

'''CREATE CUSTOMER STRIPE ACCOUNT TO USING NAME '''

class stripeCustomer:
        
        def create_stripe_customer(user_id):
            user            =  Registration.objects.exclude(Q(user_is_delete=1)&Q(user_role_id=2)).get(user_id=user_id)     
            response_data   =  stripe.Customer.create(description="client added to stripe",
                                       email = user.user_email,
                                       name  = user.user_first_name+' '+user.user_last_name)
            cust_id         = response_data['id']
            # code to create ephemeral key to stripe
            update_data = {
                        "user_stripe_id" : cust_id, 
                       }    
            user_serializer = RegisterSerializer(instance=user,data=update_data,partial=True)
            if user_serializer.is_valid():
                  user_serializer.save()
                  return True