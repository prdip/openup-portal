#IMPORT SERIALIZERS
from rest_framework import serializers



#IMPORT MODELS FROM SGSP APPLICATION

from .models import Registration,Session,ForgotPassword,UserRole,VehicleDetails,Payment



# REGISTRATION SERIALIZER
class RegisterSerializer(serializers.ModelSerializer):

    user_first_name          =   serializers.CharField()
    user_middle_name         =   serializers.CharField()
    user_last_name           =   serializers.CharField()
    user_email               =   serializers.EmailField()
    user_phone_number        =   serializers.CharField()
    user_password            =   serializers.CharField()
    create_at                =   serializers.DateTimeField()
    user_role                =   serializers.PrimaryKeyRelatedField(queryset = UserRole.objects.all())
    user_is_delete           =   serializers.BooleanField(default=0,allow_null=True)


    # Field level validation  
    # def validate_user_first_name(self,value):
    #     if any (value.isdigit() for value in value):
       
    #         raise serializers.ValidationError("User name must be string")
    #     else:
    #         return value    

    

    class Meta:

        model = Registration

        fields = ('user_first_name','user_middle_name', 'user_last_name', 'user_email','user_phone_number',
                  'user_password','create_at','user_role','user_is_delete')




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
                    'token',
                    'status','timestamp',
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


        fields = ('user_card_no','card_cvv','card_name','card_validity',
              'card_type','created_at','update_at','is_delete')
