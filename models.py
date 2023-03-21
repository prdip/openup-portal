# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class ForgotPassword(models.Model):
    forgot_pass_id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=254)
    status = models.IntegerField()
    token = models.CharField(max_length=300)
    timestamp = models.CharField(max_length=100)
    user = models.ForeignKey('UserRegistration', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'forgot_password'


class Jobstype(models.Model):
    status_id = models.AutoField(primary_key=True)
    status_name = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'jobstype'


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    user_card_no = models.BigIntegerField()
    card_cvv = models.IntegerField()
    card_name = models.CharField(max_length=250)
    card_validity = models.DateTimeField()
    card_type = models.CharField(max_length=250)
    created_at = models.DateTimeField()
    update_at = models.DateTimeField(blank=True, null=True)
    is_delete = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'payment'


class UserRegistration(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_first_name = models.CharField(max_length=150)
    user_middle_name = models.CharField(max_length=150)
    user_last_name = models.CharField(max_length=150)
    user_email = models.CharField(unique=True, max_length=254)
    user_phone_number = models.CharField(max_length=12)
    user_password = models.CharField(max_length=550)
    create_at = models.DateTimeField()
    update_at = models.DateTimeField(blank=True, null=True)
    user_is_delete = models.IntegerField()
    user_role = models.ForeignKey('Userrole', models.DO_NOTHING, blank=True, null=True)
    current_location_lat = models.FloatField(blank=True, null=True)
    current_location_long = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_registration'


class UserSessions(models.Model):
    session_id = models.AutoField(primary_key=True)
    session_user_email = models.CharField(max_length=254)
    session_token = models.CharField(unique=True, max_length=500)
    session_exp = models.DateTimeField()
    session_status = models.IntegerField()
    session_created_at = models.DateTimeField()
    session_updated_at = models.DateTimeField(blank=True, null=True)
    session_is_delete = models.IntegerField()
    session_user = models.ForeignKey(UserRegistration, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'user_sessions'


class Userjob(models.Model):
    job_id = models.AutoField(primary_key=True)
    current_location_lat = models.FloatField()
    current_location_long = models.FloatField()
    vehicle_details = models.CharField(max_length=400)
    vehicle_modification = models.CharField(max_length=500)
    vehicle_license = models.CharField(max_length=100)
    created_at = models.DateTimeField()
    update_at = models.DateTimeField(blank=True, null=True)
    is_delete = models.IntegerField()
    job_status_id = models.IntegerField(unique=True)
    user_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'userjob'


class Userrole(models.Model):
    role_created_at = models.DateTimeField()
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50)
    role_module = models.CharField(max_length=100, blank=True, null=True)
    role_permission = models.CharField(max_length=100, blank=True, null=True)
    role_status = models.IntegerField()
    role_is_delete = models.IntegerField()
    role_updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'userrole'


class VehicleModel(models.Model):
    vehicle_id = models.AutoField(primary_key=True)
    vehicle_details = models.CharField(max_length=200)
    vehicle_license = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(UserRegistration, models.DO_NOTHING)
    vehicle_modification = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField()
    update_at = models.DateTimeField(blank=True, null=True)
    vehicle_status = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'vehicle_model'
