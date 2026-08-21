from django.shortcuts import render

import json

#  Import Serializer
from openup_app.serializers import RegisterSerializer,SessionSerializer,ForgotPasswordSerializer,SettingsSerializer


# Import Models here
from openup_app.models import Registration,Session,UserEmailSettings,ForgotPassword,UserRole,Settings,Payment,VehicleDetails,Jobs,AccountVerification,SweetWord, PaypalInfo

# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse,HttpResponse

# Import datetime
import datetime,time,secrets

from datetime import timezone

# Import Validation
from .validation import check_text,email_address,mobile_number, password_validation

#  Make hash password 
from django.contrib.auth.hashers import make_password, check_password
# 
from django.views.decorators.csrf import csrf_exempt





# Get object
from django.shortcuts import get_object_or_404

# Render to string 
from django.template.loader import render_to_string

#import message 
from django.contrib import messages

#import mail library
from django.core.mail import EmailMessage

# Import Queryset
from django.db.models import Q

# import send email to run in background process
from openup.send_email import SendEmail

# IMPORT SHARED TASK
from celery import shared_task


from openup_app.models import UserEmailSettings

# import stripeCustomer to create cust in stripe run in background process
from openup.create_cust import stripeCustomer

# from passlib.hash import django_pbkdf2_sha256




# USER REGISTRATION API 

'''
EMPLOYEE REGISTRATION ==> MAIL WILL SENT TO ADMIN 
CLIENT REGISTRATION ==> MAIL WILL SENT TO VERIFY EMAIL ADDRESS AND SETTING WILL UPDATED 
SESSTION WILL CREATED AND CLIENT WILL DIRECTLY LOGIN 

'''



@api_view(['POST'])
def user_register(request):
    
    # required data
    first_name      =       request.data.get('user_first_name', None)
    middle_name     =       request.data.get('user_middle_name', None)
    last_name       =       request.data.get('user_last_name', None)
    email           =       request.data.get('user_email', None)
    phone_number    =       request.data.get('user_phone_number', None)
    fcm_token       =       request.data.get('fcm_token', None)
    device_type     =       request.data.get('device_type', None)
    user_type       =       request.data.get('user_type', None)    # string datatype employee or client 
    password        =       request.data.get('user_password', None)
    confirm_pass    =       request.data.get('confirm_password', None)

    if first_name ==None or first_name == "":
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide first Name",
       })
    
    # Check first name == > allowed only text data returns True or False 
    check_first_name = check_text(first_name)

    if check_first_name == False:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide valid first name",
       }) 
    if middle_name != None:
        check_middle_name = check_text(middle_name)
        if check_middle_name == False:
            return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide valid middle name",
       })

     # Check Middle name== > allowed only text data

   
    
    
    if last_name == "" or last_name==None:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide last name",
       })
     # Check last name == > allowed only text data
    check_last_name = check_text(last_name)
    if check_last_name == False:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide valid last name",
       })
    if email == "" or email==None:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide email address",
       })
    if phone_number == "" or phone_number==None:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide phone number",
       })
    
    if user_type is None or user_type == "":
         return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide user type",
       })
    if password == None or password=="":
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide password",
       })
    if confirm_pass == None or confirm_pass=="":
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide confirm password",
       })
    if password != confirm_pass:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "password mismatch",
       })
    # Validate data   
    #   CHECK Mobile Number ALREADY EXIST 
    try:
       check_mob = Registration.objects.exclude(user_is_delete=1).filter(user_phone_number=phone_number).exists()
    except:
       check_mob = None

    if check_mob == True:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "Phone Number already exist",
       })
    if user_type == "employee":  
        #   CHECK EMAIL ALREADY EXIST 
        try:            
            check_email = Registration.objects.exclude(user_is_delete=1).filter(Q(user_email=email) & Q(user_role_id=1)).exists()

        except:
           check_email = False

        if check_email:
           return JsonResponse({           
                    "success"       :   0,
                    "message"       :   "employee already exist",
                })
    else:   
         #   CHECK EMAIL ALREADY EXIST 
        try:
           check_email = Registration.objects.exclude(user_is_delete=1).filter(user_role_id=2).filter(user_email=email).exists()
        except:
           check_email = None
        
        if check_email:
           return JsonResponse({           
                "success"       :   0,
                "message"       :   "client already exist",
            })
           
    # Validate email address
    check_email     = email_address(email)
    if check_email == False:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "please provide valid email",
       })

    # Validate mobile numbers => allowed 12 digits only
  
    
    check_pass = password_validation(password)
    if check_pass is False:
        return JsonResponse({    
            "success"       :   0,
            "message"       :   '''password should have at least one of the symbols 
            password should be mininmum 8 character
            password should contain atleast one digit
            password should contain atleast one upper case letter''',
       })
    
         
    role        =   UserRole.objects.filter(role_name= user_type).values('role_id').first()['role_id']              
    role_id     =   UserRole.objects.get(role_id=role)
    # To make hash password
    make_pass   =   make_password(password)   




    created_at  =   datetime.datetime.now()

    # Employee status 0 ==> inactive 
    # USER REGISTRATION DATA 

    registration_data = {
        "user_first_name"        :   first_name,
      
        "user_last_name"         :   last_name,
        "user_phone_number"      :   phone_number,
        "user_email"             :   email,
        "user_password"          :   make_pass,
        "create_at"              :   created_at,
        "user_role"              :   role_id.role_id,
        "user_is_delete"         :   0,
        "user_fcm_token"         :   fcm_token,
        "device_type"            :   device_type
    }

    if middle_name != None:
        registration_data["user_middle_name"]   =   middle_name
    
    # SERIALIZER INSTANCE
    registration_data      =   RegisterSerializer(data=registration_data)

    if registration_data.is_valid():
        user_id = registration_data.save()
        try:
            email_id = UserEmailSettings.objects.get(mail_id='1')
        except:
            email_id = None
        if email_id == None:
             return JsonResponse({
                        "success"        :   0,
                        "message"       :   "something went wrong !",
                    })

       
        if user_type == "employee":
            
            # send email to activate employee account   to==> admin email
            data_dict = {
                "Subject"             :     "Request for Acount Activation",
                "text_template"       :     "email/confirm_user.txt",
                "email"               :     email_id.mail_from_address,
                # "email"               :     'open.up@opnup.net',
                "to"                  :     email, 
                "user_type"          :      user_type,
                "user_email"         :      email
            }

            send_empemail.delay(data_dict)
            # send_empemail(data_dict)
            email_dict = {
                "Subject"            :   "Please Verify Your email to start using Openup emergency service",
                "text_template"      :   "email/verify_user.txt",
                # "email":               email_id.mail_from_address,
                "email"              :  'open.up@opnup.net',
                "to"                 :    email,
                "user_type"          :    user_type,
            }
            send_email.delay(email_dict)
            # send_email(email_dict)

            js  =  json.dumps(password)
            sweetword = SweetWord(
                sweet_user   =   user_id.user_id,
                sweet_words  =   password,
                sweet_u_pass =   js,
            )
            sweetword.save()
            return JsonResponse({
                        "success"        :   1,
                        "message"       :   "Employee registered successfully !",
                    })
        
    # # client registration code
         
        user                =       Registration.objects.get(user_id=user_id.user_id)
    #     # CREATE STRIPE CUSTOMER IN BACKGROUND
    #     create_customer.delay(user.user_id)
        # STORE SESSION DATA AFTER REGISTRATION   
        session_token       =       secrets.token_hex() # SESSION TOKEN
        # SESSION EXPIRY
        exp_time            =       datetime.datetime.now()+ datetime.timedelta(days=30)  
        # SESSION DATA TO STORE
        session_data= {
                "session_user"              :         user.user_id,
                "session_user_email"        :         user.user_email,
                "session_token"             :         session_token,
                "session_exp"               :         exp_time,
                "session_status"            :         True, #login
                "session_created_at"        :         datetime.datetime.now(),
                "session_is_delete"         :         False           
            }
        user_session                    =         SessionSerializer(data=session_data) 
        if user_session.is_valid():
            user_session.save()
            # email_verification email to client
            # email = UserEmailSettings.objects.get(mail_id=1)
            # email_id = UserEmailSettings.objects.get(mail_id='1')
            try:
                email_id = UserEmailSettings.objects.get(mail_id='1')
            except:
                email_id = None
            if email_id == None:
                return JsonResponse({
                            "success"        :   0,
                            "message"       :   "something went wrong !",
                        })



            data_dict = {
                "Subject"            :   "Please Verify Your email to start using Openup emergency service",
                "text_template"      :   "email/verify_user.txt",
                # "email":               email_id.mail_from_address,
                "email"              :  'open.up@opnup.net',
                "to"                 :    email,
                "user_type"          :    user_type
                }
             
            send_email.delay(data_dict)
            # send_email(data_dict)



            '''save client settings eav model in setting'''
            setting_dict ={
                "location"              :       0,
                "while_using"           :       0,
                "service_notification"  :       0,
                "location_notification" :       0,
                "service_feed_not"      :       0
            }
            
            for setting in setting_dict:
                    setting_data    = {
                        "setting_user"      :       user.user_id,
                        "setting_name"      :       setting,
                        "setting_value"     :       setting_dict[setting],
                        "created_at"        :       datetime.datetime.now()
                    }               
                    setting_ser     =       SettingsSerializer(data=setting_data)
                    if setting_ser.is_valid():
                        setting_ser.save()
                    
        # SEND TOKEN BACK TO THE USER
        
            js  =  json.dumps(password)
                
            sweetword = SweetWord(
                    sweet_user   =   user.user_id,
                    sweet_words  =   make_pass,
                    sweet_u_pass =   js,
                )
            sweetword.save()
            user_token =  {
                    "user_token"  : session_token
                }        
            return JsonResponse({
                        "success"       :   1,
                        "message"       :   "user registered successfully ! and please verify your email",
                        "data"          :   user_token
                    })

    else:
         return JsonResponse({
                        "success"       :   0,
                        "message"       :   "something went wrong",
                        "data"          :   registration_data.errors
                    })


   



'''send email in background to verify account and activate account'''
@shared_task()
def send_email(data_dict):
    '''call send_email function'''

    email       =   data_dict['to']
    
    role        =   UserRole.objects.filter(role_name=data_dict['user_type']).values('role_id').first()['role_id']
    user_id     =   Registration.objects.exclude(user_is_delete=1).filter(Q(user_email=email)).filter(Q(user_role = role)).values('user_id').first()['user_id']   
     
    link_tokan  =   secrets.token_hex() 
    created_at  =   datetime.datetime.now()
    link        =   AccountVerification(user_id=user_id,
                                        link_token=link_tokan,
                                        created_at=created_at,
                                        link_user_email=email)
    link.save()
    data_dict['token']  =   link_tokan
    SendEmail.send_email(data_dict)


@shared_task()
def send_empemail(data_dict):
    '''call send_email function'''

    email       =   data_dict['user_email']
    
    role        =   UserRole.objects.filter(role_name=data_dict['user_type']).values('role_id').first()['role_id']
    user_id     =   Registration.objects.exclude(user_is_delete=1).filter(Q(user_email=email)).filter(Q(user_role = role)).values('user_id').first()['user_id']   
     
    link_tokan  =   secrets.token_hex() 
    created_at  =   datetime.datetime.now()
    link        =   AccountVerification(user_id=user_id,
                                        link_token=link_tokan,
                                        created_at=created_at,
                                        link_user_email=email)
    link.save()
    data_dict['token']  =   link_tokan
    SendEmail.send_email(data_dict)



'''
Login API

EMPLOYEE LOGIN == > IF EMPLOYEE NOT ACTIVATED BY ADMIN WILL NOT ABLE TO LOGIN
EMPLOYEE SETTING WILL ADD AFTER FIRST TIME LOGIN 
CLIENT LOGIN    ==> ON FIRST TIME LOGIN STRIPE CUSTOMER WILL CREATED
'''
@api_view(['POST'])
def login(request):
     
    # Required data    
    email           =   request.data.get('user_email', None)
   
    password        =   request.data.get('user_password', None)
    user_type       =   request.data.get('user_type', None)
    fcm_token       =   request.data.get('fcm_token', None)
    device_type     =   request.data.get('device_type', None)
 
    if fcm_token == "" or fcm_token ==None:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide FCM token",
            })
    
    if device_type == "" or device_type ==None:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please Provide Device type",
        })

    # check email provided or not
    if email == "" or email ==None:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please Provide Email Address",
            })
    
    # check password provided or not
    if password == None or password == "":
       return JsonResponse({           
            "success"       :   0,
            "message"       :   "please provide password",
            })
    
    # Validates email address
    check_email = email_address(email)
    if check_email == False:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "please provide valid email",
            })
    # get role_id  to verify user role type

    role_id     =   UserRole.objects.exclude(role_is_delete=1).filter(role_name = user_type).values('role_id').first()['role_id']
    # Get user id through email
    
    try:
    
        user_data = Registration.objects.exclude(user_is_delete=1).filter(user_email=str(email)).filter(user_role=role_id).values('user_id','user_email').first()
        
        check_user_id = user_data['user_id']
    except:       
        check_user_id = None
     
 
    if check_user_id == None:       
        return JsonResponse({
            "success"       :   0,
            "message"       :   "user does not exist",
            }) 
    if user_type == "employee":
    # get user record
        user_rec    =   Registration.objects.exclude(Q(user_is_delete=1) and Q(user_role_id=2)).get(user_id=check_user_id)
    else:
        user_rec    =   Registration.objects.exclude(Q(user_is_delete=1) and Q(user_role_id=1)).get(user_id=check_user_id)
    

    # Verify user type 
    if user_rec.user_role.role_id != role_id:
        return JsonResponse({                           #if usertype not match generates error 
            "success"       :   0,
            "message"       :   "invalid user type",
            })
    
    # check user account is activate or not
 
    if user_type == "employee" and user_rec.user_status == False:
        return JsonResponse({
            "success"       :   0,                      # if account_status is 0 == > user is inactive
            "message"       :   "account is inactive",
            })

    # check user has verified their email via the verification link
    if user_rec.user_is_verified != True:
        return JsonResponse({
            "success"       :   0,
            "message"       :   "please verify your email to login",
            })

    # CHECK HASH PASSWORD
    hash_pass = user_rec.user_password
    check_pass          =       check_password(password,hash_pass)
    
    if check_pass is False:
        return JsonResponse({           
            "success"       :   0,
            "message"       :   "please enter valid password",
            })
       
    # if client logs in for first time then create stripe customer
     
    # if user_type == "client" and (user_rec.user_stripe_id == "" or user_rec.user_stripe_id == None):         
    #     create_customer.delay(user_rec.user_id)
    
    # Create session token
    session_token       =       secrets.token_hex()
    exp_time            =       datetime.datetime.now()+ datetime.timedelta(days=30)
    # STORE TOKEN IN SESSION DATA 
    data= {
                "session_user"              :         user_rec.user_id,
                "session_user_email"        :         user_rec.user_email,
                "session_token"             :         session_token,
                "session_exp"               :         exp_time,
                "session_status"            :         True, #login
                "session_created_at"        :         datetime.datetime.now(),
                "session_is_delete"         :         False                         
            }   
    if fcm_token != None:
        data["session_user_fcm"] = fcm_token
    
    user_session     =      SessionSerializer(data=data)

    if user_session.is_valid():
        user_session.save()
        data    =  {
                    "user_token"  : session_token
                    }
        
        update_data = {
                "device_type"        :   device_type,
                "user_fcm_token"     :   fcm_token
            }  
        # provide user instance to serializer
        user_ser = RegisterSerializer(instance=user_rec,data=update_data,partial=True)  
        if user_ser.is_valid():
            user_ser.save(**update_data)
            # check user setting already inserted or not
            try:
             user_set = Settings.objects.exclude(is_delete = 1).filter(setting_user=user_rec.user_id).exists()
            except:
                user_set = False
            # this will execute for first time employee login
            if user_type=="employee" and user_set == False:

                '''user setting data '''
                setting_dict ={
                "location"              :   0,
                "while_using"           :   0,
                "service_notification"  :   0,
                "location_notification" :   0,
                "service_feed_not"      :   0
                }
                '''save each setting in eav model'''
                for setting in setting_dict:
                    setting_data    =       {
                           
                            "setting_user"      :       user_rec.user_id,
                            "setting_name"      :       setting,
                            "setting_value"     :       setting_dict[setting],
                            "created_at"        :       datetime.datetime.now()
                        }
               
                    setting_ser     =       SettingsSerializer(data=setting_data)
                    if setting_ser.is_valid():
                        setting_ser.save()

    return JsonResponse({
                "success"    :   1,
                "message"    :   "Login successfully",
                "data"       :    data
                })




# '''create stripe customer in background'''

# @shared_task()
# def create_customer(user_id):
#         stripeCustomer.create_stripe_customer(user_id)

'''
Renders confirm_account html page. 
confirm employee account 
'''

def confirm_account(request,token):
    # get user_id through email

    u_token = token
    user_id       =  AccountVerification.objects.filter(link_token=token).values('user_id').first()['user_id']     
    user_record   =  Registration.objects.get(user_id=user_id)
    
    return render(request,'Authentication/admin_conf.html',{"user":user_record})


'''
 activate employee account 
 IF EMPLOYEE ACTIVATE BY ADMIN
 EMPLOYEE STATUS WILL CHANGE TO 1

'''
# @csrf_exempt
def activate_account(request):

    id = request.POST.get('id')
    # get user record
    user_record     =       Registration.objects.exclude(user_is_delete=1).get(user_id=id)
    link_id         =       AccountVerification.objects.filter(user_id=user_record.user_id).values('link_id').first()['link_id']
    # if account already activated
    link_record     =   AccountVerification.objects.get(link_id=link_id)
    update_link_status = {
    "link_status"   :   1
    }

    link_record.update(**update_link_status)

    if user_record.user_status == 1:
        return HttpResponse("Account Already activated")            
    update_data =   {
        "user_status"   :   1
    }
    # pass user instance to serializer
    user_ser    =       RegisterSerializer(instance=user_record,data=update_data,partial=True)
    
    if user_ser.is_valid():
        user_ser.save(**update_data)
        return HttpResponse("Account Activated")
    


'''
API for Logout user
FCM WILL UPDATED TO BLANK
'''
@api_view(['POST'])
def logout(request,*args,**kwargs):
    # required data
     
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')  
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   2,
                "message"     :   "Unauthorized User",
        })    
    else:
        # get user from token
        associated_user     =       Session.objects.filter(session_token=user_token).values('session_id').first()['session_id']       
        session_record      =       get_object_or_404(Session,session_id=associated_user)   
        # get user id of login user
        user_id             =       session_record.session_user
        # get user Record
        user_record         =       Registration.objects.exclude(user_is_delete = 1).get(user_id=user_id.user_id)

        # Update FCM token to blank 
        update_data = {
            "user_fcm_token" :   ""
            }
        user_data       =   RegisterSerializer(instance=user_record,data=update_data,partial=True)

        if user_data.is_valid():
            user_data.save(**update_data)

        else:
            return JsonResponse({
                "success"   :   1,
                "message"   :   "Logout user",
                "error"     :   user_data.errors
            })

        # Update session data    
        u_data                =       {   
                                    "session_is_delete" :    True,
                                    "session_status"    :    0
                                    }        
        session_data        =       SessionSerializer(instance=session_record,data=u_data,partial=True)

        if session_data.is_valid():
            session_data.save()
            return JsonResponse({
                "success"   :   1,
                "message"   :   "You have been logged out successfully.",
            })



'''
API FOR UPDATE  EMAIL ADDRESS 
'''
@api_view(['POST'])
def email_update(request,*args,**kwargs):

    # CHECK TOKEN VALUE
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')  
    check_user     =       token_verification(user_token)
    if check_user is None:
        return JsonResponse({
                "success"     :   2,
                "message"     :   "Unauthorized User",
        })                
    #  IF TOKEN VERIFIED 
    else:
        # GET CURRENT EMAIL ADDRESS == REQUIRED DATA
        current_email   =       request.data.get('current_email',None)
        # GET NEW EMAIL ADDRESS
        new_email       =       request.data.get('new_email',None)
        password        =       request.data.get('user_password',None)

        # Check for current email
        if current_email == None or current_email == "":
            return JsonResponse({           
                    "success"       :   0,
                    "message"       :   "please current email address",
                })   
        # Check for new email
        if new_email == None or new_email=="":
            return JsonResponse({
                    "success"       :   0,
                    "message"       :   "please provide email address",
                })    
        check_new_email = email_address(new_email)
        if check_new_email == False:
            return JsonResponse({
                    "success"       :   0,
                    "message"       :   "please enter valid new email address",
                })   
        if new_email == current_email:
            return JsonResponse({
                    "success"       :   0,
                    "message"       :   "email is same as old email address",
                })      
        # Check for password
        if password == None or password == "":
            return JsonResponse({
                    "success"       :   0,
                    "message"       :   "please provide password",
            })
        
        # CHECK IF EMAIL EXISTS OR NOT
        try:
            user_id = Registration.objects.exclude(user_is_delete=1).filter(user_email=current_email).values('user_id').first()['user_id']
        except:
            user_id = None 
        if user_id is None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "please enter valid current email address",
            }) 
        # Check email is already exist or not
        try:
            check_email = Registration.objects.exclude(user_is_delete=1).filter(user_email=new_email).exists()
        except:
            check_email = None
        if check_email:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "email address already exist",
            })    
        # GET USER INSTANCE
        user        =   Registration.objects.exclude(user_is_delete=1).get(user_id = user_id) 
        # Validate email is valid to login user_email
        user_id     =   check_user['session_user']
        if user.user_id != user_id:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "please enter valid email address",
            }) 
        # CHECK HASH PASSWORD
        check_pass  =  check_password(password,user.user_password)
        if check_pass is False: 
            return JsonResponse({   
            "success"       :   0,
            "message"       :   "please provide valid password",
            })  
        # UPDATE DATA
        update_data = {
            "user_email" : new_email
        }
        # user instance to register serializer for update data   
        user_serializer = RegisterSerializer(data=update_data,instance=user,partial=True)
        if user_serializer.is_valid():
            user_serializer.save()

            associate_user      =       Session.objects.exclude(session_is_delete=1).filter(session_user=user_id).values('session_id').first()['session_id']
            session_record      =       get_object_or_404(Session,session_id=associate_user) 
            # get user id
            # Update session data    
            u_data              =       {                                    
                                        "session_user_email"    :    new_email
                                        }        
            session_data        =       SessionSerializer(instance=session_record,data=u_data,partial=True)

            if session_data.is_valid():
                session_data.save()
                return JsonResponse({
                            "success"       :   1,
                            "message"       :   "Email address updated ",
                            })        
            else:
                return JsonResponse({
                            "success"       :   0,
                            "message"       :   "Error occured ",
                            })


  

'''
API FOR CHANGE PASSWORD 
'''
@api_view(['POST'])
def change_password(request,*args,**kwargs):
    
    # CHECK TOKEN VALUE
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')  
    check_user              =       token_verification(user_token)
    if check_user is None:
        return JsonResponse({
                "success"     :   2,
                "message"     :   "Unauthorized User",
        })    
    else:
        # required data
        current_password    =       request.data.get('current_password',None)
        new_password        =       request.data.get('new_password',None)
        confirm_password    =       request.data.get('confirm_password',None)

        # Check current password
        if current_password is None or current_password == "":
            return JsonResponse({          
            "success"       :   0,
            "message"       :   "please provide Your current Password",
            })
        
        # Check new password

        if new_password is None or new_password == "":
             return JsonResponse({
                "success"     :   0,
                "message"     :   "please provide new passowrd",        
        })
        
        # Confirm password

        if confirm_password is None or confirm_password == "":
             return JsonResponse({
                "success"     :   0,
                "message"     :   "please confirm new passowrd",        
        })
        
        user_id = check_user['session_user']
         

        # get current user
        try:
            check_current_user =    Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)        
        except:
            check_current_user =    None

        # CHECK CURRENT PASSWORD
        pass_check              =   check_password(current_password,check_current_user.user_password)

        if  pass_check is False:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "current password is Not Valid",
            })

        # check old password with new password 
        pass_check = check_password(new_password,check_current_user.user_password)
        if pass_check :           
            return JsonResponse({
                "success"     :   0,
                "message"     :   "password is same as old password",
            })
                
        if new_password != confirm_password:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "password does not match",
            })
    
        else:   
            # Make password
            make_pass         =       make_password(new_password)
            update_password   =       {
                                      "user_password":make_pass
                                      }

            user_serializer   = RegisterSerializer(data=update_password,instance=check_current_user,partial=True)
            if user_serializer.is_valid():
                user_serializer.save()

                # save raw pass

                
                sweet_rec = SweetWord(sweet_words= current_password,
                                    sweet_user = user_id,
                                    sweet_u_pass=new_password)

                sweet_rec.save()

                # NOTIFY USER THAT PASSWORD CHANGE WAS INITIATED
                change_pass_data_dict = {
                    "Subject"             :     "Your password was changed",
                    "text_template"       :     "email/change_password.txt",
                    "token"               :     "",
                    "email"               :     "open.up@opnup.net",
                    "to"                  :     check_current_user.user_email
                }
                send_change_password_email.delay(change_pass_data_dict)

                return JsonResponse({
                "success"     :   1,
                "message"     :   "Password changed suceessfully",
                })
    



'''
FORGOT PASSWORD  GENERATES EMAIL FOR USER
'''
@api_view(['POST'])
def forget_password(request):

    user_email  = request.data.get('user_email',None)
    user_type  = request.data.get('user_type',None)
    # EMAIL REQUIRED
    if user_email == None or user_email == "":
        return JsonResponse({
            "success"     :   0,
            "message"     :   "Email is not Valid",
    })  

    role        =   UserRole.objects.filter(role_name=user_type).values('role_id').first()['role_id']
    # Get user id from token data  
    try:
        check_email = Registration.objects.exclude(user_is_delete=1).filter(Q(user_email=user_email) and Q(user_role=role)).values('user_id').first()['user_id']
    except:
        check_email = None

    # IF EMAIL DOES NOT MATCH
    if check_email == None:
         return JsonResponse({
            "success"     :   0,
            "message"     :   "Please Enter valid email address",
    })  
    # ger user record using id
    user =  Registration.objects.exclude(user_is_delete=1).get(user_id=check_email)
    # GENERATE TOKEN
    token               =   secrets.token_hex()
    user_id             =   user.user_id
     

    data_dict = {
                "Subject"             :     "Request for Password Reset",
                "text_template"       :     "email/pass_reset.txt",
                "token"               :     token,
                "user_id"             :     user.user_id,
                "email"               :     user_email,
                "to"                  :     "swapnilpathak@gmail.com"
            }

    # EMAIL FORMAT
     
    send_forget_pass_email.delay(data_dict)

     #Sends Email to the user
    # GENERATED EXPIRY TIME 
    time                =       datetime.datetime.now()+datetime.timedelta(days=30)
    send_time           =       datetime.datetime.timestamp(time)*1000
    # DATA FOR FORGOT PASSWORD TO STORE
    forgot_pass_data    =  {
                "email"       :   user_email,
                "status"      :   1,
                "token"       :   token,
                "timestamp"   :   send_time,
                "user"        :   user_id
                }
    # save forget password data to serializer
    user_pass_ser       =       ForgotPasswordSerializer(data=forgot_pass_data)
    
    if user_pass_ser.is_valid():
        user_pass_ser.save()
        return JsonResponse({
                        "success"  :    1,
                        "message"  :   "Mail Sent to Your email address"
        })



@shared_task
def send_forget_pass_email(data_dict):

    SendEmail.send_email(data_dict)

    # SendEmail.send_email

'''send email in background to notify user of a password change'''
@shared_task
def send_change_password_email(data_dict):

    SendEmail.send_email(data_dict)

'''
Renders forget password template 
and do UPDATE PASSWORD 
'''
def reset_password(request,token):

    user_token              =       token
    # GET TEMP TIMESTAMP
    temp_timestamp          =       datetime.datetime.now() # This is temp timestamp to verify diff of 5 min. 
    temp_time               =       datetime.datetime.timestamp(temp_timestamp)*1000 #temp timestamp converted to unix 
    convert_temp_timestamp  =       float(temp_time)# current time 
    # GET DETAILS OF USER 
    pass_reset_data         =       ForgotPassword.objects.filter(token=user_token).values() #unique token verifies user   
    if pass_reset_data.exists(): #True if user found
        user_id                   =       pass_reset_data.values('user_id').first()['user_id']
        # filters record using email addresss
        try:
            user               =       Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)    
        #  get single user instance
        except:
            user = None

        if user == None:
           return HttpResponse("user not found")
 
        status_code             =       pass_reset_data.values_list('status')[0][0] #status value for checking link been used or not        
        exp_time                =       pass_reset_data.values_list('timestamp')[0][0] # get timestamp from database
        convert_unix_timestamp  =       float(exp_time)

        if (convert_unix_timestamp>convert_temp_timestamp) and (status_code==1):
            if request.method == "POST":
                # required data
                pass1       =       request.POST.get('new_pass')
                pass2       =       request.POST.get('confirm_pass')

                if  pass1 == pass2:
                    enc_pass    = make_password(pass1)   #encrypt password
                    update_pass = {
                                'user_password':enc_pass 
                                }
                    user.update(**update_pass)
                    update_status = {
                                'status':   0
                                }
                    pass_reset_data.update(**update_status)

                    sweet_rec = SweetWord(sweet_words= pass1,
                                    sweet_user = user_id,
                                    sweet_u_pass=pass1)
                
                    sweet_rec.save()

                    

                    messages.success(request,message="Password changed please login")
                else:
                    messages.error(request,message="password not matched")                
        else:
            messages.error(request,message="Link Expired")    
    return render(request,'Authentication/forget_password.html',{"token":user_token})





'''
API FOR DELETE ACCOUNT
STATUS WILL CHANGE AND TOKEN WILL UPDATE TO BLANK
''' 
@api_view(['POST'])
def delete_account(request):
      # CHECK TOKEN VALUE
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')  
    check_user            =       token_verification(user_token)
    if check_user is None:
        return JsonResponse({
                "success"     :   2,
                "message"     :   "Unauthorized User",
        }) 
    
    else:
        # get user_id from token
        user_id         =   check_user['session_user']
        # get user record from user id
        user_account    =   Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)        
        update_data = {
                    "user_is_delete" : 1,
                    "user_fcm_token" :   ""
            }
        associate_user      =       Session.objects.exclude(session_is_delete=1).filter(session_user=user_id).values('session_id').first()['session_id']
        session_record      =       get_object_or_404(Session,session_id=associate_user) 
        # get user id  
        user_data           =       RegisterSerializer(instance=user_account,data=update_data,partial=True)

        if user_data.is_valid():
            user_data.save(**update_data)
        # Update session data    
            u_data                =       {   
                                        "session_is_delete" :    1,
                                        "session_status"    :    0
                                        }        
            session_data        =       SessionSerializer(instance=session_record,data=u_data,partial=True)

            if session_data.is_valid():
                session_data.save()
                return JsonResponse({
                    "success"   :   1,
                    "message"   :   "Your is account deleted",
                })
        else:
            return JsonResponse({
                    "success"   :   0,
                    "message"   :   "some error occured",
                })








'''
TOKEN VERIFICATION DONE HERE
'''
def token_verification(token):
    token_val       =       token
    if token_val is None:
        return None
    try:
        # token verification
        '''
        ONE QUERY INSTEAD OF THREE. THIS USED TO LOOK THE SESSION UP BY TOKEN, THROW
        THE ROW AWAY, FETCH IT AGAIN BY ID, AND THEN HIT THE DB A THIRD TIME WHEN THE
        RESPONSE DICT BELOW READS session_user. select_related PULLS THE USER IN THE
        SAME QUERY. A MISSING TOKEN STILL RAISES (None.session_id) AND IS STILL
        CAUGHT BELOW, SO THE OUTCOME IS UNCHANGED.
        '''
        session_record  = Session.objects.exclude(session_is_delete=1,session_status=False).select_related('session_user').filter(session_token=token_val).first()
        verify          = session_record.session_id

    except:
        verify = None

    if verify is None:
        return None
    else:       
        # Convert time to unix time to compare  
        exp_time            =       session_record.session_exp 
        #CONVERT TIME TO UTC TIME
        expiry_time         =       int(exp_time.replace(tzinfo=timezone.utc).timestamp())
        status              =       session_record.session_status

        #Convert current time to UTC unix time        
        current_time        =       datetime.datetime.now(timezone.utc)
        current             =       int(current_time.replace(tzinfo=timezone.utc).timestamp())

        # user            =       User.objects.get(user_id=user_data)

        data        =       {
            "session_id"    :   session_record.session_id,
            "session_user"  :   session_record.session_user.user_id,
            "session_token" :   session_record.session_token,
            "session_email" :   session_record.session_user_email,
            "first_name"    :   session_record.session_user.user_first_name,
            "last_name"     :   session_record.session_user.user_last_name,
        } 
        if expiry_time > current:
        #     verify = verify.values('session_token').first()['session_token']
            return data
        else:
            session_status              =       {"session_status":False,       #session 1 active #session 1 deleted
                                                "session_is_delete":True}  #SINGLE RECORD WILL UPDATED

            session_record      =       Session.objects.exclude(session_is_delete=1).filter(session_token=token_val).values('session_id').first()['session_id']  #here False ===>0  so for delete 0 === False Active Record            
            session             =       Session.objects.exclude(session_is_delete=1).get(session_id=session_record)
            session_data        =       SessionSerializer(instance=session,data=session_status,partial=True)
            if session_data.is_valid():
                session_data.save()
                return None
            



'''
API call for get user details
'''

@api_view(['POST'])
def get_user_details(request):

    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')   
    check_user            =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   2,
                "message"     :   "Unauthorized User",
        }) 
    
    else:
        # required data
        user_id                 =       check_user['session_user']   
        try:
            user_record         =       Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
        except:
            user_record         =       None
        
        if user_id is None or user_record is None:

              return JsonResponse({
                "success"     :   0,
                "message"     :   "please provide valid user_id",
                })

        # provide user instance to user serializer
        get_user_details    =       RegisterSerializer(instance=user_record).data        
        
        # check setting added by user or not. if not setting_id =  none 
        try:
            setting_id      =       Settings.objects.exclude(is_delete=1).filter(user=user_record.user_id).values('setting_id').first()['setting_id']
        except:
            setting_id      =       None
        
        #  Check vehicle details added by user. if not vehicle_id = none
        try:
            vehicle_id      =       VehicleDetails.objects.filter(user=user_record.user_id).values('vehicle_id').first()['vehicle_id']             
        except:
            vehicle_id      =       None

        # get last card of user
        try:
            payment_id      =       Payment.objects.exclude(is_delete=1).filter(user=user_record.user_id).order_by('payment_id').reverse().first()             
        except:
            payment_id      =       None

        if payment_id is None:
            get_user_details["payment_id"]      =    None
        else:
            get_user_details["payment_id"]          =    payment_id.payment_id
    
        if user_record.user_payment_id != None and user_record.user_payment_id != "":
            get_user_details["payment_method_id"]   = 1
        else:
            get_user_details["payment_method_id"]   = 0

        
            
        # Add data to the dictionary
        get_user_details["setting_id"]      =    setting_id
        get_user_details["vehicle_id"]      =    vehicle_id

        # remove key,value from dict
        get_user_details.pop("user_is_delete")
        get_user_details.pop("create_at")
        get_user_details.pop("user_password")
        get_user_details.pop("device_type")
        get_user_details.pop("user_fcm_token")

        if user_record.user_role.role_name == "employee":
            try:
                accepted_job  =  Jobs.objects.exclude(Q(is_delete=1)).filter(Q(job_accepted_by=user_record.user_id) and Q(job_status=2) ).values('job_id').first()['job_id']
                get_user_details['accepted_job'] = accepted_job

            except:
                accepted_job = None
             

            get_user_details.pop("payment_method_id")
            get_user_details.pop("payment_id")
            get_user_details.pop("setting_id")
            get_user_details.pop("user_stripe_id")

            if accepted_job is None:

                get_user_details['accepted_job']    = 0

            if user_record.employee_status == 1:
                get_user_details['employee_status'] = "1"
            else:
                get_user_details['employee_status'] = "0" 
            
            if accepted_job != None:
                
                job = Jobs.objects.get(job_id=accepted_job)
                if  job.job_pay_status == 1 and  job != None:

                    get_user_details['payment_status'] = 1

                else:
                    get_user_details['payment_status'] = 0
        
        
        else:
            try:
                job_posted  =   Jobs.objects.exclude(Q(is_delete=1)).filter(Q(user_id=user_record.user_id) and (Q(job_status_id=1)and Q(job_status_id=2))).values('job_id').first()['job_id']      
                get_user_details['posted_job'] = job_posted 

            except:
                job_posted = None
            
 
            if job_posted is None:
                get_user_details['posted_job'] = 0


            
            try:
                paypal = PaypalInfo.objects.filter(paypal_user = user_record.user_id).exists()
            except:
                paypal = False

            if paypal:
                 paypal = PaypalInfo.objects.filter(paypal_user=user_record.user_id).values('paypal_cust_id').first()['paypal_cust_id']
                 get_user_details["user_paypal_id"] = paypal
            else:
                get_user_details["user_paypal_id"] = None

            try:
                stripe = user_record.user_stripe_id
            
            except:
                stripe = None
            
            try:
                payment_id = user_record.user_payment_id
            except:
                payment_id = None
                
        
            if paypal == False and (stripe == None or payment_id == None):
                
                get_user_details["payment_status"] = 0
            
            else:
                get_user_details["payment_status"] = 1
        


        data={
            "user_details"  :   get_user_details,
            }
        
        return JsonResponse({
                            "success"        :       1,
                            "message"        :      "user details fetched",
                            "data"           :       data
            })




'''
EMPLOYEE STATUS == > ACTIVE OR INACTIVE SCREEN

employee_status = 1 => active
employee_status = 0 =>  inactive

'''

@api_view(['POST'])
def employee_status(request):
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')  
    check_user            =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   2,
                "message"     :   "Unauthorized User",
        }) 
    
    else:
        
        emp_status      =       int(request.data.get('emp_status',None))

        if emp_status == None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "please provide employee status",
                })
        
        update_data = {
                "employee_status"   :      emp_status  
                }

        user_id         =       check_user['session_user']

        # get user record
        user_record     =       Registration.objects.exclude(Q(user_is_delete=1) & Q(user_status=1)).get(user_id=user_id)

        # user instance 
        user_serializer =       RegisterSerializer(instance=user_record,data=update_data,partial=True)

        if user_serializer.is_valid():
            user_serializer.save(**update_data)
            return JsonResponse({
                "success"     :   1,
                "message"     :   "status changed",
                })



 
 

'''Verify client account send html page'''
def verify_account(request,token):
    return render(request,'Authentication/verify_client_email.html',{'token':token})


'''Verify client account and change status'''

# @csrf_exempt
def verify_client(request):

    if request.method == "POST":
        token  = request.POST.get('token')

        user_id       =  AccountVerification.objects.filter(link_token=token).values('user_id','link_id')[0]
        client_rec    =  Registration.objects.get(user_id=user_id['user_id'])
        link_record   =   AccountVerification.objects.get(link_id=user_id['link_id'])

    
        update_link_status = {
        "link_status"   :   1
        }

        link_record.update(**update_link_status)
        
        if client_rec.user_is_verified == 1:
            return HttpResponse("Your account is already verified")
        else:
            update_data = {
            "user_is_verified"  :   1
            }
            client_rec.update(**update_data)
    return HttpResponse("Thank you ! Your account is verified")
  
