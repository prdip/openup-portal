# Create your tests here.
from django.test.testcases import TransactionTestCase

from django.test import TestCase

from rest_framework.test import APIRequestFactory,RequestsClient,APITestCase

from openup_app.models import Registration,UserRole

import datetime


from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver


from django.urls import reverse
from rest_framework import status



'''
        ()
       
        '''
        


class TestSetup(APITestCase):

    def setUp(self):
        
        self.register_url = reverse('registration')
        self.register_url = reverse('login')
        self.user_data = {'user_first_name':'swapnil666','user_middle_name':'shriram','user_last_name':'pathak',
                                                 'user_email':'swapnil@gmail.com','user_phone_number':'888888888','user_password':'pass','create_at' : datetime.datetime.now(),
                                                'user_type':"employee",'location_latitude':22.75,'location_longitude':70.55,'device_type':0,'user_fcm_token':'fcmtoken for employee','user_status':0}

        return super().setUp()
        
    def tear_Down(self):
           

        return super().tearDown()
    









# # Create your tests here.
# from django.test.testcases import TransactionTestCase

# from django.test import TestCase

# from rest_framework.test import APIRequestFactory,RequestsClient,APITestCase

# from openup_app.models import Registration,UserRole

# import datetime


# from django.contrib.staticfiles.testing import StaticLiveServerTestCase
# from selenium.webdriver.common.by import By


# from django.urls import reverse
# from rest_framework import status


# # class RegistrationTest(TransactionTestCase):
# #     reset_sequences = True

# #     def setUp(self):
# #         pass
        
#         # client = UserRole.objects.all()
#         # print(client)
#         # serialized_rollback = True
       
#         # Registration.objects.create(user_first_name='swapnil',user_middle_name='shriram',user_last_name='pathak',user_email='swapnil@gmail.com',user_phone_number=888888888,user_password='pass',create_at = datetime.datetime.now(),
#         #                                         user_role=1,location_latitude=22.75,location_longitude=70.55,device_type=0,user_fcm_token='fcmtoken for employee',user_status=0)

     
#     # def test_registration(self):

#         # try:
#         #     user_role = UserRole.objects.get(role_id=1)
#         # except:
#         # #     user_role = None
#         # client = UserRole.objects.all()
#         # print(client)
#         # serialized_rollback = True
#         # user_role =  self.client.objects.filter(role_name="employee").values()

#         # data = {'user_first_name':'swapnil','user_middle_name':'shriram','user_last_name':'pathak',
#         #                                          'user_email':'swapnil@gmail.com','user_phone_number':'888888888','user_password':'pass','create_at' : datetime.datetime.now(),
#         #                                         'user_role':1,'location_latitude':22.75,'location_longitude':70.55,'device_type':0,'user_fcm_token':'fcmtoken for employee','user_status':0}

#         # factory = APIRequestFactory()


#         # response = factory.post('api/registration',data=data,format='json')

        

       
#         # return True
#                 # Registration.objects.create(user_first_name='swapnil',user_middle_name='shriram',user_last_name='pathak',user_email='swapnil@gmail.com',user_phone_number=888888888,user_password='pass',create_at = datetime.datetime.now(),
#         #                                         user_role=user_role.role_id,location_latitude=22.75,location_longitude=70.55,device_type=0,user_fcm_token='fcmtoken for employee',user_status=0)

#         # 1 ==> employee
#         # reg  =  Registration()
#         # response = reg.post('api/registration', {'user_first_name':'swapnil','user_middle_name':'shriram','user_last_name':'pathak',
#         #                                          'user_email':'swapnil@gmail.com','user_phone_number':'888888888','user_password':'pass','create_at' : datetime.datetime.now(),
#         #                                         'user_role':1,'location_latitude':22.75,'location_longitude':70.55,'device_type':0,'user_fcm_token':'fcmtoken for employee','user_status':0})
           
                                    
                                    
#         # response.status_code



# '''
#         ('user_middle_name':'shriram','user_last_name':'pathak',
#                                                  'user_email':'swapnil@gmail.com','user_phone_number':'888888888','user_password':'pass','create_at' : datetime.datetime.now(),
#                                                 'user_type':"employee",'location_latitude':22.75,'location_longitude':70.55,'device_type':0,'user_fcm_token':'fcmtoken for employee')
       
#         '''
        


# class TestSetup(APITestCase):

#     def setUp(self):
        
#         self.register_url = reverse('registration')
#         self.register_url = reverse('login')
#         self.user_data = {'user_first_name':'swapnil','user_status':0}

#         return super().setUp()
        
#     def tear_Down(self):
           

#         return super().tearDown()
    

# class RegisrationTest(TestSetup):

#     def test_registration(self):

       
#         res = self.client.post(self.register_url,self.user_data,format="json")
#         import pdb
#         pdb.set_trace()
        
        
#         self.assertEqual(res.status_code,200)
        










