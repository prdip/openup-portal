from django.db import models

# Create your models here.






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




class Registration(models.Model):

    user_id                 =    models.AutoField(primary_key=True)
    user_first_name          =   models.CharField(max_length=150)
    user_middle_name         =   models.CharField(max_length=150)
    user_last_name           =   models.CharField(max_length=150)
    user_email               =   models.EmailField(unique=True)
    user_phone_number        =   models.CharField(max_length=12)
    user_password            =   models.CharField(max_length=550)
    user_role                =   models.ForeignKey(UserRole,on_delete=models.CASCADE,null=True)
    create_at                =   models.DateTimeField()
    update_at                =   models.DateTimeField(null=True,blank=True)
    user_is_delete           =   models.BooleanField(default=0)





    class Meta:

        db_table = "user_registration"

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

