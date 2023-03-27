
from django.urls import reverse

from rest_framework.test import APITestCase,APIClient

from django.test.testcases import TransactionTestCase

from openup_app.models import UserRole,Registration
from openup_api.views.auth_views import user_register

import datetime

import pdb 
import json


'test case for user registration'

class RegisrationTest(APITestCase):


    def setUp(self):

        

        # self.factory = APIRequestFactory()
        # self.view = user_register
        # # self.url = reverse('registration')
        pass


    def test_registration(self):
        allow_database_queries = True
        self.client = APIClient()


        self.user_role = UserRole.objects.create(role_name="employee",role_created_at=datetime.datetime.now(),role_status=1)
        self.user_role.save()
        
        role_id  = UserRole.objects.filter(role_name="employee").values('role_id').first()['role_id']
        user_role= UserRole.objects.get(role_id=role_id)

        self.create_emp = Registration.objects.create(user_first_name='swapnil',
                     user_middle_name ='shriram',
                     user_last_name    ='pathak',
                     user_email         ='swapnil@gmail.com',
                     user_phone_number   =888888888888888888888888888888,
                     user_password      ='pass',                                              
                                         location_latitude=22.75,
                     location_longitude   =70.55,
                     device_type         =0,
                     user_fcm_token       ='fcmtoken for employee',
                     user_role_id          = user_role.role_id,
                     user_status         =0,
                     create_at=datetime.datetime.now()


        )
        self.create_emp.save()


           # print
        # user_data = {'user_first_name'      :'swapnil',
        #              'user_middle_name'     :'shriram',
        #              'user_last_name'       :'pathak',
        #              'user_email'           :'swapnil@gmail.com'
        #              ,'user_phone_number'   :8888888888,
        #              'user_password'        :'pass',
        #              'confirm_password'     :'pass',                                                
                    
        #              'location_latitude'    :22.75,
        #              'location_longitude'   :70.55,
        #              'device_type'          :0,
        #              'user_fcm_token'       :'fcmtoken for employee',
        #               'user_type'            :"employee",
        #              'user_status'          :0}

        # res = self.client.post(reverse('registration'),user_data)

        

        # response = self.view(res)
        # print("Status Code",res.status_code,'\n',"Response is:",str(res.content))

class LoginTest(APITestCase):

    def test_login(self):
        email       =         "test@gmail.com"
        user        =         Registration.objects.filter(email=email).values('user_id').first()['user_id']
        user_record =         Registration.objects.get(user_id=user)


        
        # user_data = {
           
        #     "user_email"    :   "test@gmail.com",
        #     "user_password" :   "pass",
        #     "user_type"     :   "employee",
        #     "fcm_token"     :   "fcm_token",
        #     "device_type"   :   1
        # }
        

        # res = self.client.post(reverse('login'),user_data)
        # print("Status Code",res.status_code,'\n',"Response is:",str(res.content))



        




      

     
