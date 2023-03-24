#IMPORT SERIALIZERS
from rest_framework import serializers



#IMPORT MODELS FROM SGSP APPLICATION

from .models import Registration,Session,ForgotPassword,UserRole,VehicleDetails,Payment,Jobs,JobsType,Settings,Feedback



# REGISTRATION SERIALIZER
class RegisterSerializer(serializers.ModelSerializer):

    user_first_name          =   serializers.CharField()
    user_middle_name         =   serializers.CharField()
    user_last_name           =   serializers.CharField()
    user_email               =   serializers.EmailField()
    user_phone_number        =   serializers.CharField()
    user_password            =   serializers.CharField()
    location_latitude        =   serializers.FloatField(allow_null=True,required=False)
    location_longitude       =   serializers.FloatField(allow_null=True,required=False)
    create_at                =   serializers.DateTimeField()
    employee_status          =   serializers.BooleanField(default=0,allow_null=True)
    user_role                =   serializers.PrimaryKeyRelatedField(queryset = UserRole.objects.all())
    user_is_delete           =   serializers.BooleanField(default=0,allow_null=True)
    device_type              =   serializers.IntegerField(required=False,allow_null=True)   # 0 == > Anaroid  1==> IOS
    user_fcm_token           =   serializers.CharField(required=False,allow_null=True,allow_blank=True   )


    # Field level validation  
    # def validate_user_first_name(self,value):
    #     if any (value.isdigit() for value in value):
       
    #         raise serializers.ValidationError("User name must be string")
    #     else:
    #         return value    

    def update(self,instance,validated_data):     
        demo = Registration.objects.get(user_id=instance.user_id)
        demo.update(**validated_data)
        return demo
    

    class Meta:
        model = Registration

        fields = ('user_first_name','user_middle_name', 
                  'user_last_name', 'user_email',
                  'user_phone_number','user_password',
                  'location_latitude','location_longitude',
                  'create_at','user_role','user_is_delete',
                  'device_type','user_fcm_token','employee_status')




#SESSION SERIALIZER

class SessionSerializer(serializers.ModelSerializer):

    session_user            =           serializers.PrimaryKeyRelatedField(queryset = Registration.objects.all())
    session_user_email      =           serializers.EmailField()
    session_token           =           serializers.CharField()
    session_exp             =           serializers.DateTimeField()
    session_status          =           serializers.BooleanField()
    session_created_at      =           serializers.DateTimeField()
    session_is_delete       =           serializers.BooleanField()
    session_user_fcm        =           serializers.CharField(required=False)

    class Meta:
        model = Session
        fields = ('session_user','session_user_email',
                    'session_token','session_exp',
                    'session_status','session_created_at',
                    'session_is_delete','session_user_fcm')


    def create(self,validated_data):     
        return Session.objects.create(**validated_data)



# FORGOT PASSWORD SERIALIZER    
    
class ForgotPasswordSerializer(serializers.ModelSerializer):

    user               =        serializers.PrimaryKeyRelatedField(queryset = Registration.objects.all())
    email              =        serializers.EmailField()
    status             =        serializers.BooleanField()
    token              =        serializers.CharField(max_length=300)
    timestamp          =        serializers.CharField(max_length=100)

    class Meta:
        
        model = ForgotPassword

        fields = ('user','email',
                'token','status',
                'timestamp',
                    )


# VEHICLE DETAILS MODEL

class VehicleSerializer(serializers.ModelSerializer):

    user                    =       serializers.PrimaryKeyRelatedField(queryset = Registration.objects.all())
    vehicle_details         =       serializers.CharField()
    vehicle_modification    =       serializers.CharField()
    vehicle_license         =       serializers.FileField(required = False)  
    created_at              =       serializers.DateTimeField()
    
    
    class Meta:
        model = VehicleDetails

        fields = ('user','vehicle_details',
                    'vehicle_license',
                   'vehicle_modification',
                   'created_at'
                    )


# PAYMENT SERIALIZER

class PaymentSerializer(serializers.ModelSerializer):

    user            =       serializers.PrimaryKeyRelatedField(queryset = Registration.objects.all())
    user_card_no    =       serializers.CharField()
    card_cvv        =       serializers.IntegerField()
    card_name       =       serializers.CharField()
    card_validity   =       serializers.DateTimeField()
    card_type       =       serializers.CharField()
    created_at      =       serializers.DateTimeField()
    update_at       =       serializers.DateTimeField(required=False)
    is_delete       =       serializers.BooleanField(default=0)

    class Meta:
        model = Payment


        fields = ('user','user_card_no','card_cvv',
                  'card_name','card_validity',
                    'card_type','created_at',
                    'update_at','is_delete')




#  Job Serializer

class JobsTypeSerializer(serializers.Serializer):
    status_name     =       serializers.CharField()

    class Meta:
        db_table = 'jobstype'


# Job Serializer
class JobsSerializer(serializers.Serializer):
    job_id                   =   serializers.PrimaryKeyRelatedField( read_only=True)
    job_type                 =   serializers.CharField()
    user                     =   serializers.PrimaryKeyRelatedField(queryset = Registration.objects.all(),allow_null=True)
    location_latitude        =   serializers.FloatField(required=False)
    location_longitude       =   serializers.FloatField(required=False)
    job_accepted_by          =   serializers.CharField(required=False)
    vehicle_details          =   serializers.CharField()
    vehicle_modification     =   serializers.CharField()
    vehicle_license          =   serializers.FileField(required=False,allow_null=True)
    created_at               =   serializers.DateTimeField()
    is_delete                =   serializers.BooleanField(default=0)
    job_status               =   serializers.PrimaryKeyRelatedField(queryset = JobsType.objects.all())

    def create(self,validated_data):
        n = Jobs.objects.create(**validated_data)
        id = n.pk
        return id 
    
    def update(self,instance,validated_data):     
        demo = Jobs.objects.get(job_id=instance.job_id)
        demo.update(**validated_data)
        return demo

    # def update(self, instance, validated_data):

    class Meta:
        model = Jobs
        fields = ('job_id','job_type','user','location_latitude',
                  'location_longitude','vehicle_details',
                  'vehicle_modification','vehicle_license',
                  'created_at','is_delete','job_status','job_accepted_by')





# Setting Serializer

class SettingsSerializer(serializers.Serializer):

    setting_user    =    serializers.PrimaryKeyRelatedField(queryset = Registration.objects.all())
    setting_name    =    serializers.CharField()
    setting_value   =    serializers.BooleanField()
    created_at      =    serializers.DateTimeField()
   

    def create(self,validated_data):     
        return Settings.objects.create(**validated_data)
    
    # def update(self,validated_data):     
    #     return Settings.objects.update(**validated_data)

    def update(self,instance,validated_data):     
        demo = Settings.objects.get(setting_id=instance.setting_id)
        demo.update(**validated_data)
        return demo


    class Meta:
        model = Settings

        fields = ('setting_user','created_at',
                  'setting_name','setting_value')




# FEEDBACK SERIALIZER

class FeedbackSerializer(serializers.Serializer):

    feedback_job           =      serializers.PrimaryKeyRelatedField(queryset = Jobs.objects.all())
    feedback_user          =      serializers.PrimaryKeyRelatedField(queryset = Registration.objects.all())
    feedback_stars         =      serializers.FloatField(default=1)
    feedback_comment       =      serializers.CharField(max_length=500)
    created_at             =      serializers.DateTimeField()
    
    def create(self,validated_data):     
        return Feedback.objects.create(**validated_data)
    
    
    class Meta:
        model = Feedback
        fields = ('feedback_job','feedback_user','feedback_stars',
                  'feedback_comment','created_at')