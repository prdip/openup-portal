from django.db import models

# Create your models here.

import datetime

# USER  ROLES
class UserRole(models.Model):
    choice = (   
            ('client','client'),            
            ('employee','employee'),
            )

    role_id             =       models.AutoField(primary_key=True)
    role_name           =       models.CharField(choices=choice,max_length=50)
    role_module         =       models.CharField(max_length=100,null=True)
    role_permission     =       models.CharField(max_length=100,null=True)
    role_status         =       models.BooleanField()
    role_created_at     =       models.DateTimeField(auto_created=True)
    role_is_delete      =       models.BooleanField(default=0)
    role_updated_at     =       models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'userrole'
    
    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()



#  User Registration Model 

class Registration(models.Model):

    user_id                  =   models.AutoField(primary_key=True)
    user_first_name          =   models.CharField(max_length=150)
    user_middle_name         =   models.CharField(max_length=150, null=True)
    user_last_name           =   models.CharField(max_length=150)
    user_email               =   models.EmailField()
    user_phone_number        =   models.CharField(max_length=12)
    user_password            =   models.CharField(max_length=1000)
    user_role                =   models.ForeignKey(UserRole,on_delete=models.CASCADE,null=True)
    create_at                =   models.DateTimeField()
    location_latitude        =   models.FloatField(null=True)
    location_longitude       =   models.FloatField(null=True)
    device_type              =   models.IntegerField(null=True,default=1)   # 1 == > Anaroid  2==> IOS
    user_fcm_token           =   models.TextField(null=True,blank=True)
    user_stripe_id           =   models.CharField(max_length=500,null=True,blank=True)  #CLIENT STRIPE ID 
    user_payment_id          =   models.CharField(max_length=500,null=True,blank=True)  #CLIENT PAYMENT METHOD ID
    user_payment_type        =    models.CharField(max_length=150,null=True)
    user_status              =   models.BooleanField(null=True,default=0)   #STATUS OF EMPLOYEE ACTIVE BY ADMIN
    user_is_verified         =   models.BooleanField(default=1)
    employee_status          =   models.BooleanField(null=True,default=0)   #STATUS OF EMPLOYEE ACTIVE SCREEN OR INACTIVE SCREEN
    update_at                =   models.DateTimeField(null=True,blank=True)
    user_is_delete           =   models.BooleanField(default=0)

    class Meta:

        db_table = "users"

    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()

    

#Session Management


class Session(models.Model):
    session_id                  =           models.AutoField(primary_key=True)
    session_user                =           models.ForeignKey(Registration,on_delete=models.CASCADE)
    session_user_email          =           models.EmailField()
    session_token               =           models.CharField(max_length=150,unique=True)
    session_exp                 =           models.DateTimeField()
    session_status              =           models.BooleanField()    
    session_created_at          =           models.DateTimeField()
    session_updated_at          =           models.DateTimeField(null=True)
    session_is_delete           =           models.BooleanField(default=1)
    session_user_fcm            =           models.CharField(max_length=500,null=True)

    class Meta:
        db_table = 'user_sessions'

    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()

    
    #  Forget Password
    
class ForgotPassword(models.Model):
    forgot_pass_id     =        models.AutoField(primary_key=True)
    user               =        models.ForeignKey(Registration,on_delete=models.CASCADE,null=True)
    email              =        models.EmailField()
    status             =        models.BooleanField()
    token              =        models.CharField(max_length=300)
    timestamp          =        models.CharField(max_length=100)

    class Meta:
        db_table = 'forgot_password'

    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()




# change filename 
import os
def file_name(instance, filename):
        ext     =   filename.split('.')[-1]
        name    =   filename.split('.')[0]
        count   =   0

        for i in range(0, len(name)):  
            if(name[i] != ' '):  
                count = count + 1

        if count >=12:
              name = str(name)[0:12]

        time     =      (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

        filename =      "'%s','%s',.%s'" % (name,str(time),ext)
        return os.path.join('licenses',filename)



# VEHICLE DETAILS MODEL

class VehicleDetails(models.Model):

    vehicle_id              =       models.AutoField(primary_key=True)
    user                    =       models.ForeignKey(Registration,on_delete=models.CASCADE)
    vehicle_license         =       models.FileField(upload_to=file_name,blank=True,null=True)  #licenses

    year                     =      models.CharField(max_length=5,null=True)
    model                    =      models.CharField(max_length=10,null=True)
    colour                   =      models.CharField(max_length=10,null=True)
    any_mod                  =      models.BooleanField(default=0)
    window_tint              =      models.BooleanField(default=0)
    make                     =      models.CharField(max_length=100,null=True)

    created_at              =       models.DateTimeField()
    update_at               =       models.DateTimeField(null=True)
    vehicle_status          =       models.BooleanField(default=0)

    
    class Meta:
        db_table = 'vehicle_model'


    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()


# PAYMENT MODEL WILL STORE CARD INFORMATION

class Payment(models.Model):

    payment_id              =       models.AutoField(primary_key=True)
    user                    =       models.ForeignKey(Registration,on_delete=models.CASCADE,null=True)
    user_card_no            =       models.CharField(max_length=20)
    card_customer_id        =       models.CharField(max_length=50,null=True)
    card_method_id          =       models.CharField(max_length=50,null=True)
    card_cvv                =       models.IntegerField()
    card_name               =       models.CharField(max_length=250)
    card_validity           =       models.DateTimeField()
    card_type               =       models.CharField(max_length=250)
    created_at              =       models.DateTimeField()
    update_at               =       models.DateTimeField(null=True)
    is_delete               =       models.BooleanField(default=0)


    class Meta:
        db_table = 'payment'

    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()




# Job status Model
'''
1==> ACTIVE
2==> ACCEPTED
3==> COMPLETED
4==> CANCELED
'''

class JobsType(models.Model):
    status_id       =       models.AutoField(primary_key=True)
    status_name     =       models.CharField(max_length=20)

    class Meta:
        db_table = 'jobstype'



# Jobs Model

class Jobs(models.Model):

    choice = (
        ('service','service'),
        ('emergency','emergency'),
        )
        
    job_id                   =       models.AutoField(primary_key=True) 
    job_type                 =       models.CharField(max_length=20,choices=choice,default="service")

    # status of job 1 == >active 2==> accepted 3==>completed

    job_status               =   models.ForeignKey(JobsType,on_delete=models.CASCADE)
    user                     =   models.ForeignKey(Registration,on_delete=models.CASCADE)
    location_latitude        =   models.FloatField()
    location_longitude       =   models.FloatField()
    # vehicle_details          =   models.CharField(max_length=300)
    # vehicle_modification     =   models.CharField(max_length=400)
    vehicle_license          =   models.FileField(upload_to=file_name, null=True)
    job_accepted_by          =   models.CharField(max_length=31,null=True)
    job_payment_id           =   models.CharField(max_length=100,null=True)  # GENERATED AND SAVED AFTER SUCCESSFUL PAYMENT 
    job_pay_status           =   models.BooleanField(default=0)
    job_time                 =   models.CharField(max_length=100,null=True)    #1==> SUCCESS 0==> NO PAYMENT
    job_distance             =   models.CharField(max_length=100,null=True) 
    
    year                     =   models.CharField(max_length=5,null=True)
    model                    =   models.CharField(max_length=10,null=True)
    colour                   =   models.CharField(max_length=10,null=True)
    any_mod                  =   models.BooleanField(default=0)
    window_tint              =   models.BooleanField(default=0)
    make                     =   models.CharField(max_length=100,null=True)

    created_at               =   models.DateTimeField()
    update_at                =   models.DateTimeField(null=True)
    is_delete                =   models.BooleanField(default=0)

    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()


    class Meta:
        db_table = 'userjob'





class JobLogs(models.Model):
    log_id      =   models.AutoField(primary_key=True)
    job         =   models.CharField(max_length=100,null=True)
    log_msg     =   models.CharField(max_length=200,null=True)
    cancel_by   =   models.CharField(max_length=200,null=True)
    created_at  =   models.DateTimeField()
    updated_at   =   models.DateTimeField(null=True)
    is_delete   =   models.BooleanField(default=0)

    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()


    class Meta:
        db_table = 'job_log'




# SETTING MODEL EAV STRUCTURE
class Settings(models.Model):

    setting_id      =    models.AutoField(primary_key=True)         
    setting_user    =    models.ForeignKey(Registration,on_delete=models.CASCADE)
    setting_name    =    models.CharField(max_length=50,default="user")
    setting_value   =    models.BooleanField(default=0)
    created_at      =    models.DateTimeField()
    update_at       =    models.DateTimeField(null=True)
    is_delete       =    models.BooleanField(default=0)


    class Meta:
        db_table = 'user_setting'

    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()


# SAVE ALERTS

class Alerts(models.Model):
    alert_id         =      models.AutoField(primary_key=True)
    alert_job        =      models.ForeignKey(Jobs,on_delete=models.CASCADE)
    alert_users      =      models.CharField(max_length=500)
    alert_title      =      models.CharField(max_length=500)
    alert_messages   =      models.CharField(max_length=500)
    alert_status     =      models.BooleanField(default=0)
    created_at       =      models.DateTimeField()
    update_at        =      models.DateTimeField(null=True)
    is_delete        =      models.BooleanField(default=0)

    class Meta:
        db_table = 'alerts'



#  FEEDBACK MODEL

class Feedback(models.Model):

    feedback_id            =      models.AutoField(primary_key=True)
    feedback_job           =      models.OneToOneField(Jobs,on_delete=models.CASCADE)
    feedback_user          =      models.ForeignKey(Registration,on_delete=models.CASCADE)
    feedback_stars         =      models.FloatField()
    feedback_comment       =      models.CharField(max_length=500)
    feedback_status        =      models.BooleanField(default=0)
    created_at             =      models.DateTimeField()
    update_at              =      models.DateTimeField(null=True)
    is_delete              =      models.BooleanField(default=0)


    class Meta:
        db_table = 'feedback'




#  PAYMENT FAILED INFO MODEL

class PaymentFailedInfo(models.Model):
    payment_status_id       =   models.AutoField(primary_key=True)
    user_id                 =   models.CharField(max_length=10)
    job_id                  =   models.CharField(max_length=10)
    payment_fail_type       =   models.CharField(max_length=500,null=True)
    payment_fail_response   =   models.TextField(null=True)
    payment_fail_code       =   models.CharField(max_length=500,null=True)
    payment_fail_message    =   models.TextField(null=True)

    created_at              =   models.DateTimeField()

    class Meta:
        db_table = 'paymentfailedinfo'




    


class AccountVerification(models.Model):

    link_id     =       models.AutoField(primary_key=True)
    user_id     =       models.CharField(max_length=10)
    link_user_email =   models.CharField(max_length=50)
    link_token  =       models.CharField(max_length=500)
    link_status =        models.BooleanField(default=0)
    created_at  =       models.DateTimeField()
    update_at   =       models.DateTimeField(null=True)
    is_delete   =       models.BooleanField(default=0)

    class Meta:
        db_table = 'accountverification'


    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()


class SweetWord(models.Model):

    sweet_id     =  models.AutoField(primary_key=True)
    sweet_user   =  models.CharField(max_length=50)
    sweet_words  =  models.CharField(max_length=500)
    sweet_u_pass =  models.CharField(max_length=500)

    class Meta:
        db_table = 'sweetwords'
    
    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()







class UserEmailSettings(models.Model):


    mail_id         =    models.AutoField(primary_key=True)
    mail_user_id    =    models.ForeignKey(Registration,on_delete=models.CASCADE,null=True)
    mail_mailer     =    models.CharField(max_length=50) 
    mail_host       =    models.CharField(max_length=50)
    mail_user_name       =    models.CharField(max_length=50)
    mail_user_pass       =    models.CharField(max_length=50)
    mail_encryption     =      models.CharField(max_length=50)

    mail_from_address   =   models.CharField(max_length=50)
    mail_from_name      =   models.CharField(max_length=50)

    mail_port           =   models.IntegerField()
    mail_status         =   models.BooleanField()
    is_delete           =   models.BooleanField()
    created_at          =   models.DateTimeField()
    update_at           =   models.DateTimeField(null=True)



    class Meta:
        db_table = 'user_email_settings'





# Save paypal valut id and customer id 

class PaypalInfo(models.Model):

    paypal_info_id      =   models.AutoField(primary_key=True)
    paypal_user         =   models.ForeignKey(Registration,on_delete=models.CASCADE)
    paypal_valut_id     =   models.CharField(max_length=50)
    paypal_response     =   models.TextField(default="text")
    paypal_cust_id      =   models.CharField(max_length=100)
    is_delete           =   models.BooleanField()
    created_at          =   models.DateTimeField()
    update_at           =   models.DateTimeField(null=True)



    class Meta:
        db_table = 'paypal_cust_info'


# save webhook data 

class WebhookData(models.Model):

    webhook_id          =   models.AutoField(primary_key=True)
    webhook_type        =   models.CharField(max_length=150,default="request")
    webhook_data        =   models.TextField()
    is_delete           =   models.BooleanField()
    created_at          =   models.DateTimeField()
    update_at           =   models.DateTimeField(null=True)



    class Meta:
        db_table = 'webhook_data'



class SuccessPayments(models.Model):

    pay_id  = models.AutoField(primary_key=True)
    pay_user= models.CharField(max_length=100)
    pay_type= models.CharField(max_length=100,null=True)
    pay_job = models.CharField(max_length=1000)
    pay_response = models.TextField()
    create_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sucess_payments'



class Images(models.Model):
    img_id      =   models.AutoField(primary_key=True)
    img_type    =   models.IntegerField(null=True)  #1-> before 2->After
    job         =   models.ForeignKey(Jobs,on_delete=models.CASCADE,null=True)
    is_delete   =   models.BooleanField()
    created_at  =   models.DateTimeField()
    update_at   =   models.DateTimeField(null=True)

    class Meta:
        db_table = 'images'





class File(models.Model):

    file_id         =   models.AutoField(primary_key=True)
    file            =   models.FileField(upload_to='attachments',null=True)
    file_name       =   models.CharField(max_length=200)
    file_path       =   models.TextField(null=True)
    file_system_name=   models.TextField(null=True)
    file_s3_path    =   models.TextField(null=True)
    file_size       =   models.IntegerField(null=True)
    file_status     =   models.IntegerField(default=1)
    file_img        =   models.ForeignKey(Images,on_delete=models.CASCADE,null=True)
    deleted_at      =   models.DateTimeField(null=True)
    created_at      =   models.DateTimeField(auto_now_add=True)
    udated_at       =   models.DateTimeField(null=True)
    is_delete       =   models.BooleanField(default=0)
    class Meta:        
        db_table = 'file'


    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()


