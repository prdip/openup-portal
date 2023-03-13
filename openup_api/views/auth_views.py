from django.shortcuts import render

#  Import Serializer
from openup_app.serializers import RegisterSerializer,SessionSerializer,ForgotPasswordSerializer


# Import Models here
from openup_app.models import Registration,Session,ForgotPassword,UserRole

# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse,HttpResponse

# Import datetime
import datetime,time

# import timezone 
from datetime import timedelta,timezone

# Import Validation
from .validation import check_text,email_address,mobile_number

#  Make hash password 
from django.contrib.auth.hashers import make_password, check_password

# Import Secret for token
import secrets

# Get object
from django.shortcuts import get_object_or_404

# Render to string 
from django.template.loader import render_to_string

#import message 
from django.contrib import messages

#import mail library
from django.core.mail import EmailMessage



@api_view(['POST'])
def user_register(request):
    
    # required data
    first_name      = request.data.get('user_first_name', None)
    middle_name     = request.data.get('user_middle_name', None)
    last_name       = request.data.get('user_last_name', None)
    email           = request.data.get('user_email', None)
    phone_number    = request.data.get('user_phone_number', None)
    user_type       = request.data.get('user_type', None)
    password        = request.data.get('user_password', None)
    confirm_pass    = request.data.get('confirm_password', None)

    if first_name ==None or first_name == "":
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide First Name",
       })
    
    if middle_name == "" or middle_name == None:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Middle Name",
            })
    
    if last_name == "" or last_name==None:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Last Name",
       })
    
    if email == "" or email==None:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Email Address",
       })
    if phone_number == "" or phone_number==None:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide phone_number",
       })
    
    if user_type is None or user_type == "":
         return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide User Type",
       })
    if password == None or password=="":
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Password",
       })
    if confirm_pass == None or confirm_pass=="":
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Confirm Password",
       })
    if password != confirm_pass:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Password Mismatch",
       })
    # Validate data

    # Check first name == > allowed only text data
    check_first_name = check_text(first_name)
    if check_first_name == False:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Valid First Name",
       })
           
    # Check Middle name== > allowed only text data

    check_middle_name = check_text(middle_name)
    if check_middle_name == False:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Valid Middle Name",
       })
    

    # Check last name == > allowed only text data
    check_last_name = check_text(last_name)
    if check_last_name == False:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Valid Last Name",
       })
    
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
        
    #   CHECK EMAIL ALREADY EXIST 
    try:
       check_email = Registration.objects.exclude(user_is_delete=1).filter(user_email=email).exists()
    except:
       check_email = None
    
    if check_email:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Email Already exist",
       })
       
    # Validate email address  ==> Validate email address
    check_email = email_address(email)
    if check_email == False:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Valid Email",
       })

    # Validate mobile numbers => allowed 12 digits only
    check_mobile_no = mobile_number(phone_number)
    if check_mobile_no is False:     
        return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Valid Moile Number",
       })
    # Get Role id from role type
    role        =   UserRole.objects.filter(role_name=user_type).values('role_id').first()['role_id']        
    role_id     =   UserRole.objects.get(role_id=role)

    # To make hash password
    make_pass = make_password(password)

    # Created date is current date
    created_at = datetime.datetime.now()
    # Employee status 0 ==> inactive 
    # USER REGISTRATION DATA 
    registration_data = {
        "user_first_name"        :   first_name,
        "user_middle_name"       :   middle_name,
        "user_last_name"         :   last_name,
        "user_phone_number"      :   phone_number,
        "user_email"             :   email,
        "user_password"          :   make_pass,
        "create_at"              :   created_at,
        "user_role"              :   role_id.role_id,
        "user_is_delete"         :   0

    }

    # SERIALIZER INSTANCE
    registration_data      =   RegisterSerializer(data=registration_data)

    if registration_data.is_valid():
        registration_data.save()
        time.sleep(5)
        user_id             =       Registration.objects.exclude(user_is_delete=1).filter(user_email=email).values('user_id').first()['user_id']    
        user                =       Registration.objects.get(user_id=user_id)
        
    # STORE SESSION DATA AFTER REGISTRATION   
    session_token       =       secrets.token_hex() # SESSION TOKEN
    # SESSION EXPIRY
    exp_time            =       datetime.datetime.now()+ timedelta(days=30)  
    
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
    if user_type == "employee":
        Subject             =   "Request for Password Reset"
        text_template       =   "email/confirm_user.txt"
        # EMAIL FORMAT
        email_data = {
                "email"     :   email,
                'domain'    :   '127.0.0.1:8000',
	    		'site_name' :   'Website',     #Data which will send with E-mail id
	    		'protocol'  :   'http',
            }


        myemail = render_to_string(text_template,email_data)  #Converts text file to string 
        email = EmailMessage(Subject, myemail, to=["swapnilpathak@gmail.com"])  #Formats Email message 
        email.send()  #Sends Email to the user
        return JsonResponse({
                    "success"       :   1,
                    "message"       :   "Employee Registered Successfully !",
        })

    user_session                    =         SessionSerializer(data=session_data)
    
    if user_session.is_valid():
        user_session.save()     

        # SEND TOKEN BACK TO THE USER
        user_token =  {
                "user_token"  : session_token
            }
        
        
        return JsonResponse({
                    "success"       :   1,
                    "message"       :   "Registered Successfully !",
                    "data"          :   user_token
                })
   


# Login API

@api_view(['POST'])

def login(request):
    # Required data    
    email           =   request.data.get('user_email', None)
    password        =   request.data.get('user_password', None)
    user_type       =   request.data.get('user_type', None)
    fcm_token       =   request.data.get('fcm_token', None)
    device_type     =   request.data.get('device_type', None)
    if device_type == "1":
        device_type = 1
    else:
        device_type = 0
    if fcm_token == "" or fcm_token ==None:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "Please Provide FCM Token",
       })
    
    if device_type == "" or device_type ==None:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "Please Provide Device type",
       })


    # check email provided or not
    if email == "" or email ==None:
       return JsonResponse({
            "success"       :   0,
            "message"       :   "Please Provide Email Address",
       })
    
    # check password provided or not

    if password == None or password == "":
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Password",
       })
    
    # Validates email address
    check_email = email_address(email)
    if check_email == False:
       return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please Provide Valid Email",
       })
    
    try:
        check_user_id = Registration.objects.exclude(user_is_delete=1).filter(user_email=email).values('user_id').first()['user_id']
    except:       
        check_user_id = None

    if check_user_id == None:       
        return JsonResponse({
           
            "success"       :   0,
            "message"       :   "User does not exist",
       })

    # get role_id  to verify user role type

    role_id = UserRole.objects.exclude(role_is_delete=1).filter(role_name = user_type).values('role_id').first()['role_id']
    
    # get user record
    user_rec    =   Registration.objects.exclude(user_is_delete=1).get(user_id=check_user_id)

    # Verify user type 
    if user_rec.user_role.role_id != role_id:
        return JsonResponse({                           #if usertype not match generates error 
            "success"       :   0,
            "message"       :   "invalid user type",
            })
    
    # check user account is activate or not

    if user_type == "employee" and user_rec.user_status == 0:
        return JsonResponse({           
            "success"       :   0,                      # if account_status is 0 == > user is inactive
            "message"       :   "account is inactive",
            })
    
    # CHECK HASH PASSWORD
    check_pass  =   check_password(password,user_rec.user_password)
    if check_pass is False:
        return JsonResponse({           
            "success"       :   0,
            "message"       :   "Please Enter Valid password",
            })
       
    # Create session token
    session_token       =       secrets.token_hex()
    exp_time            =       datetime.datetime.now()+ timedelta(days=30)

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
    
    user_session     =      SessionSerializer(data=data)

    if user_session.is_valid():
        user_session.save()
        data    =  {
                    "user_token"  : session_token
                    }
        
        update_data = {
                "device_type"       :   device_type,
                "user_fcm_token"     :   fcm_token
            }
        
        user_ser = RegisterSerializer(instance=user_rec,data=update_data,partial=True)
        
        if user_ser.is_valid():
            user_ser.save(**update_data)

    return JsonResponse({
                "success"    :   1,
                "message"    :   "Login successfully",
                "data"       :    data
                })




# Renders confirm account 

def confirm_account(request,email):
    
    user_id = Registration.objects.exclude(user_is_delete=1).filter(user_email=email).values('user_id').first()['user_id']
    user_record =  Registration.objects.get(user_id=user_id)
    
    return render(request,'Authentication/admin_conf.html',{"user":user_record})

# activate account 


def activate_account(request):
    id = request.POST.get('id')
    user_rec     =       Registration.objects.exclude(user_is_delete=1).get(user_id=id)
    update_data =   {
        "user_status"   :   1
    }
    user_ser    =       RegisterSerializer(instance=user_rec,data=update_data,partial=True)
    if user_ser.is_valid():
        user_ser.save(**update_data)
        return HttpResponse("Account Activated")
    
    # return 



# Logout API


@api_view(['POST'])
def logout(request,*args,**kwargs):
    # required data
    user_token      =       request.data.get('user_token',None)
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })    
    else:
        # get user from token
        associated_user     =       Session.objects.filter(session_token=user_token).values('session_id').first()['session_id']       
        session_record      =       get_object_or_404(Session,session_id=associated_user) 
        # get user id
        user_id             =       session_record.session_user
        # get user Record
        user_record         =       Registration.objects.exclude(user_is_delete = 1).get(user_id=user_id.user_id)
        
        update_data = {
            "user_fcm_token" :   ""

        }
        user_data       =   RegisterSerializer(instance=user_record,data=update_data,partial=True)

        if user_data.is_valid():
            user_data.save(**update_data)

        else:
            return JsonResponse({
                "success"   :   1,
                "message"   :   "Logout User",
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
                "message"   :   "Logout User",
            })








#  EMAIL ADDRESS UPDATE

@api_view(['POST'])
def email_update(request,*args,**kwargs):

    # CHECK TOKEN VALUE
    user_token = request.data.get('user_token',None)
    check_user              =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
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
            "message"       :   "Please Current Email Address",
       })
        
        # Check for new email

        if new_email == None or new_email=="":
            return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please provide Email Address",
        })

        # Check for password

        if password == None or password == "":
            return JsonResponse({
            "success"       :   0,
            "message"       :   "Please provide password",
       })
        
        # CHECK IF EMAIL EXISTS OR NOT
        try:
            user_id = Registration.objects.exclude(user_is_delete=1).filter(user_email=current_email).values('user_id').first()['user_id']
        except:
            user_id = None
        
        if user_id is None:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Please enter valid email address",
            })
        
        # Check email is already exist or not
        try:
            check_email = Registration.objects.exclude(user_is_delete=1).filter(user_email=new_email).exists()
        except:
            check_email = None

        if check_email:
            return JsonResponse({
                "success"     :   0,
                "message"     :   "Email address already exist",
        
            })

        # GET USER INSTANCE
        user  = Registration.objects.exclude(user_is_delete=1).get(user_id = user_id)

        # CHECK HASH PASSWORD
        check_pass =  check_password(password,user.user_password)

        if check_pass is False: 
            return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Please provide valid password",
            })
        
        # UPDATE DATA

        update_data = {
            "user_email" : new_email
        }
        
        user_serializer = RegisterSerializer(data=update_data,instance=user,partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({
           
            "success"       :   0,
            "message"       :   "Email Address Updated ",
            })
        



# CHANGE PASSWORD API

@api_view(['POST'])

def change_password(request,*args,**kwargs):
    
    # CHECK TOKEN VALUE
    user_token = request.data.get('user_token',None)
    check_user              =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })    
    else:
        
        current_password    =       request.data.get('current_password',None)
        new_password        =       request.data.get('new_password',None)
        confirm_password    =       request.data.get('confirm_password',None)

        # Check current password
        if current_password is None or current_password == "":
            return JsonResponse({          
            "success"       :   0,
            "message"       :   "Please provide Your current Password",
            })
        
        # Check new password

        if new_password is None or new_password == "":
             return JsonResponse({
                "success"     :   0,
                "message"     :   "Please provide new passowrd",        
        })
        
        # Confirm password

        if confirm_password is None or confirm_password == "":
             return JsonResponse({
                "success"     :   0,
                "message"     :   "Please confirm new passowrd",        
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
                "message"     :   "Current password is Not Valid",
            })


        pass_check = check_password(new_password,check_current_user.user_password)
        if pass_check :           
             return JsonResponse({
                "success"     :   0,
                "message"     :   "password is same as old password",
        })
                
        if new_password != confirm_password:
             return JsonResponse({
                "success"     :   0,
                "message"     :   "password Mismatch",
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
                return JsonResponse({
                "success"     :   1,
                "message"     :   "Password Changed ",
    
            })



# FORGOT PASSWORD  GENERATES EMAIL FOR USER

@api_view(['POST'])

def forget_password(request):

    user_email  = request.data.get('user_email',None)
    # EMAIL REQUIRED
    if user_email == None or user_email == "":
        return JsonResponse({
            "success"     :   0,
            "message"     :   "Email is not Valid",
    })  
    # Get user id from token data  
    try:
        check_email = Registration.objects.exclude(user_is_delete=1).filter(user_email=user_email).values('user_id').first()['user_id']
    except:
        check_email = None

    # IF EMAIL DOES NOT MATCH
    if check_email == None:
         return JsonResponse({
            "success"     :   0,
            "message"     :   "Please Enter valid email address",
    })  

    user =  Registration.objects.exclude(user_is_delete=1).get(user_id=check_email)
    # GENERATE TOKEN
    token               =   secrets.token_hex()
    user_id             =   user.user_id
    Subject             =   "Request for Password Reset"
    text_template       =   "email/pass_reset.txt"
    # EMAIL FORMAT
    data = {
            "email"     :   user.user_email,
            'domain'    :   '127.0.0.1:8000',
			'site_name' :   'Website',     #Data which will send with E-mail id
			"user"      :   user.user_id,
			'token'     :   token,
			'protocol'  :   'http',
        }


    myemail = render_to_string(text_template,data)  #Converts text file to string 
    email = EmailMessage(Subject, myemail, to=[user_email])  #Formats Email message 
    email.send()  #Sends Email to the user
    # GENERATED EXPIRY TIME 
    time                =       datetime.datetime.now()+timedelta(days=30)
    send_time           =       datetime.datetime.timestamp(time)*1000
    # DATA FOR FORGOT PASSWORD TO STORE
    forgot_pass_data    =      {
                                    "email"       :   user_email,
                                    "status"      :   1,
                                    "token"       :  token,
                                    "timestamp"   :   send_time,
                                    "user"        :   user_id
                                   }
    user_pass_ser = ForgotPasswordSerializer(data=forgot_pass_data)
    
    if user_pass_ser.is_valid():
        user_pass_ser.save()
        return JsonResponse({
                        "status"        :       1,
                        "message"        :      "Mail Sent to Your email Please Check"
        })






# UPDATE PASSWORD

# @api_view(['POST'])


def reset_password(request,token):

    user_token              =       token

    # GET TEMP TIMESTAMP
    temp_timestamp          =       datetime.datetime.now() # This is temp timestamp to verify diff of 5 min. 
    temp_time               =       datetime.datetime.timestamp(temp_timestamp)*1000 #temp timestamp converted to unix 
    convert_temp_timestamp  =       float(temp_time)# current time 
    
    # GET DETAILS OF USER 
    pass_reset_data         =       ForgotPassword.objects.filter(token=user_token).values() #unique token verifies user
    
    
    if pass_reset_data.exists(): #True if user found

        email                   =       pass_reset_data.values('email').first()['email']
        myuser_id               =       Registration.objects.exclude(user_is_delete=1).filter(user_email=email).values_list('user_id')[0][0]    
        user                    =       Registration.objects.exclude(user_is_delete=1).get(user_id=myuser_id)
        status_code             =       pass_reset_data.values_list('status')[0][0] #status value for checking link been used or not        
        exp_time                =       pass_reset_data.values_list('timestamp')[0][0] # get timestamp from database
        convert_unix_timestamp  =       float(exp_time)


        if (convert_unix_timestamp>convert_temp_timestamp) and (status_code==1):
            if request.method == "POST":
                pass1       = request.POST.get('new_pass')
                pass2       = request.POST.get('confirm_pass')

                if  pass1 == pass2:
                    enc_pass    = make_password(pass1)
                    update_pass = {
                                'user_password':enc_pass 
                                }
                    user.update(**update_pass)

                    update_status = {
                                'status':   0
                                }
                    

                    pass_reset_data.update(**update_status)

                    messages.success(request,message="Password changed")
                else:
                    messages.error(request,message="Please Enter Valid Pass")                
        else:
            messages.error(request,message="Link Expired")
    
    return render(request,'Authentication/forget_password.html',{"token":user_token})




@api_view(['POST'])
# DELETE ACCOUNT 

def delete_account(request):

      # CHECK TOKEN VALUE
    user_token            =       request.data.get('user_token',None)
    check_user            =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        }) 
    
    else:
        
        # get user_id from token
        user_id = check_user['session_user']


        user_account =  Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)     
        

        update_data = {
            "user_is_delete" : 1
        }

        user_serializer     =   RegisterSerializer(data=update_data,instance=user_account,partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({
                            "status"        :       1,
                            "message"        :      "Account deleted succesfully"
            })
















              


# TOKEN VERIFICATION DONE HERE
    

def token_verification(token):
    token_val       =       token
    if token_val is None:
        return None
    try: 
        # token verification 
        verify          = Session.objects.exclude(session_is_delete=1,session_status=False).filter(session_token=token_val).values('session_id').first()['session_id']
        session_record  = Session.objects.exclude(session_is_delete=1,session_status=False).get(session_id=verify)
        
    except:
        verify = None

    if verify is None:
        return None
    else:
        # list_result = [entry for entry in verify]   Queryset to dict
        # verify  =verify.__dict__
        # session= list_result[0]
       
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
            



#  API for location update


@api_view(['POST'])

def update_location(request):
       # CHECK TOKEN VALUE
    user_token            =       request.data.get('user_token',None)
    check_user            =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        }) 
    
    else:
            # required data
        latitude     =    request.data.get('latitude',None)
        longitude    =    request.data.get('longitude',None)

        # check for blank value
        if latitude is None:
            return JsonResponse({
                            "status"        :       0,
                            "message"        :      "Please provide lattitude"
            })


        if longitude is None:
            return JsonResponse({
                            "status"        :       0,
                            "message"        :      "Please provide lattitude"
            })
        
        user_id = check_user['session_user']
        # update data
        location_details = {
                    "location_latitude"   :     latitude,
                    "location_longitude"  :     longitude,
        }

        #instance of  user recored
        user_rec    =       Registration.objects.exclude(user_is_delete=1).get(user_id=user_id)
        # user serializer
        user_ser    =       RegisterSerializer(instance=user_rec,data=location_details,partial=True)

        data = {
                "location_details":location_details
            }
        if user_ser.is_valid():
            user_ser.save()
            return JsonResponse({
                            "status"        :       1,
                            "message"        :      "User location updated succesfully",
                            "data"          :       data
            })

