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
    user_middle_name         =   models.CharField(max_length=150)
    user_last_name           =   models.CharField(max_length=150)
    user_email               =   models.EmailField()
    user_phone_number        =   models.CharField(max_length=12)
    user_password            =   models.CharField(max_length=550)
    user_role                =   models.ForeignKey(UserRole,on_delete=models.CASCADE,null=True)
    create_at                =   models.DateTimeField()
    location_latitude        =   models.FloatField(null=True)
    location_longitude       =   models.FloatField(null=True)
    device_type              =   models.IntegerField(null=True,default=1)   # 1 == > Anaroid  2==> IOS
    user_fcm_token           =   models.CharField(max_length=500,null=True)
    user_status              =   models.BooleanField(null=True,default=0)
    employee_status          =   models.BooleanField(null=True,default=0)
    update_at                =   models.DateTimeField(null=True,blank=True)
    user_is_delete           =   models.BooleanField(default=0)
    # emp_not                  =   models.CharField(max_length=10,null=True)
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



# VEHICLE DETAILS MODEL


# change filename 
import os
def file_name(instance, filename):
        ext = filename.split('.')[-1]
        name = filename.split('.')[0]

        count = 0

        for i in range(0, len(name)):  
            if(name[i] != ' '):  
                count = count + 1;

        if count >=12:
              name = str(name)[0:12]
        time = (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                      
        filename = "'%s','%s',.%s'" % (name,str(time),ext)
        return os.path.join('licenses',filename)

class VehicleDetails(models.Model):

    vehicle_id              =       models.AutoField(primary_key=True)
    user                    =       models.ForeignKey(Registration,on_delete=models.CASCADE)
    vehicle_details         =       models.CharField(max_length=200)
    vehicle_modification    =       models.CharField(max_length=200,null=True)
    vehicle_license         =       models.FileField(upload_to=file_name,blank=True,null=True)  #licenses
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


# PAYMENT MODEL

class Payment(models.Model):

    payment_id      =       models.AutoField(primary_key=True)
    user            =       models.ForeignKey(Registration,on_delete=models.CASCADE,null=True)
    user_card_no    =       models.BigIntegerField()
    card_cvv        =       models.IntegerField()
    card_name       =       models.CharField(max_length=250)
    card_validity   =       models.DateTimeField()
    card_type       =       models.CharField(max_length=250)
    created_at      =       models.DateTimeField()
    update_at       =       models.DateTimeField(null=True)
    is_delete       =       models.BooleanField(default=0)


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
    vehicle_details          =   models.CharField(max_length=300)
    vehicle_modification     =   models.CharField(max_length=400)
    vehicle_license          =   models.FileField(upload_to=file_name, null=True)
    job_accepted_by          =   models.CharField(max_length=31,null=True)
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


class Settings(models.Model):

    setting_id      =    models.AutoField(primary_key=True)         
    setting_user            =    models.ForeignKey(Registration,on_delete=models.CASCADE)
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
    created_at             =      models.DateTimeField()
    feedback_status        =      models.BooleanField(default=0)
    update_at              =      models.DateTimeField(null=True)
    is_delete              =      models.BooleanField(default=0)


    class Meta:
        db_table = 'feedback'
