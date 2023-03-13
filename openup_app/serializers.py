#IMPORT SERIALIZERS
from rest_framework import serializers



#IMPORT MODELS FROM SGSP APPLICATION

from .models import Registration,Session,ForgotPassword,UserRole,VehicleDetails,Payment,Jobs,JobsType,Settings



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
    user_role                =   serializers.PrimaryKeyRelatedField(queryset = UserRole.objects.all())
    user_is_delete           =   serializers.BooleanField(default=0,allow_null=True)
    device_type              =   serializers.BooleanField(required=False)   # 0 == > Anaroid  1==> IOS
    user_fcm_token           =   serializers.CharField(required=False,allow_blank=True)


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

        fields = ('user_first_name','user_middle_name', 'user_last_name', 'user_email','user_phone_number',
                  'user_password','location_latitude','location_longitude','create_at','user_role','user_is_delete','device_type','user_fcm_token')




#SESSION SERIALIZER

class SessionSerializer(serializers.ModelSerializer):

    
    session_user            =           serializers.PrimaryKeyRelatedField(queryset = Registration.objects.all())
    session_user_email      =           serializers.EmailField()
    session_token           =           serializers.CharField()
    session_exp             =           serializers.DateTimeField()
    session_status          =           serializers.BooleanField()
    session_created_at      =           serializers.DateTimeField()
    session_is_delete       =           serializers.BooleanField()

    class Meta:
        model = Session
        fields = ('session_user','session_user_email',
                    'session_token','session_exp',
                    'session_status','session_created_at',
                    'session_is_delete')


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

    user_card_no    =       serializers.IntegerField()
    card_cvv        =       serializers.IntegerField()
    card_name       =       serializers.CharField()
    card_validity   =       serializers.DateTimeField()
    card_type       =       serializers.CharField()
    created_at      =       serializers.DateTimeField()
    update_at       =       serializers.DateTimeField(required=False)
    is_delete       =       serializers.BooleanField(default=0)

    class Meta:
        model = Payment


        fields = ('user_card_no','card_cvv',
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

    job_type                 =   serializers.CharField()
    user                     =   serializers.PrimaryKeyRelatedField(queryset = Registration.objects.all())
    location_latitude        =   serializers.FloatField(required=False)
    location_longitude       =   serializers.FloatField(required=False)
    job_accepted_by          =   serializers.CharField(required=False)
    vehicle_details          =   serializers.CharField()
    vehicle_modification     =   serializers.CharField()
    vehicle_license          =   serializers.FileField()
    created_at               =   serializers.DateTimeField()
    is_delete                =   serializers.BooleanField(default=0)
    job_status               =   serializers.PrimaryKeyRelatedField(queryset = JobsType.objects.all())



    def create(self,validated_data):     
        return Jobs.objects.create(**validated_data)
    
    def update(self,instance,validated_data):     
        demo = Jobs.objects.get(job_id=instance.job_id)
        demo.update(**validated_data)
        return demo

    # def update(self, instance, validated_data):



    class Meta:
        model = Jobs


        fields = ('job_type','user','location_latitude',
                  'location_longitude','vehicle_details',
                  'vehicle_modification','vehicle_license',
                  'created_at','is_delete','job_status','job_accepted_by')





# Setting Serializer




class SettingsSerializer(serializers.Serializer):

    user            =    serializers.PrimaryKeyRelatedField(queryset = Registration.objects.all())
    screen          =    serializers.BooleanField(default=1)
    location        =    serializers.BooleanField(default=1)
    only_using      =    serializers.BooleanField(default=1)
    service_not     =    serializers.BooleanField(default=1)
    location_not    =    serializers.BooleanField(default=1)
    ser_feed_not    =    serializers.BooleanField(default=1)
    created_at      =    serializers.DateTimeField()
   

    def create(self,validated_data):     
        return Settings.objects.create(**validated_data)
    
    def update(self,validated_data):     
        return Settings.objects.update(**validated_data)


    class Meta:
        model = Settings

        fields = ('user','screen','location',
                  'only_using','service_not',
                  'location_not','created_at',
                  'ser_feed_not')


        