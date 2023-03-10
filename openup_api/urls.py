from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from openup_api.views import auth_views, cms_views, force_update,vehicle_views,payment_views,job_views
from openup_api.views import setting

urlpatterns = [

# User Authentication 
  path('registration', auth_views.user_register,name='registration'),
  path('login', auth_views.login,name='login'),
  path('logout', auth_views.logout,name='logout'),
  path('delete_account', auth_views.delete_account,name='delete_account'),


# UPDATE
  path('email_update', auth_views.email_update,name='email-update'),


# Forget Password
  path('change_password', auth_views.change_password,name='change_password'),
  path('forget_password', auth_views.forget_password,name='forget_password'),
  path('reset_password/<slug:token>', auth_views.reset_password,name='reset_password'),
  

# CMS LINKS
  path('cms_details', cms_views.cms_details,name='cms_details'),

#  CMS PAGES
  path('copyright_page', cms_views.copyright_page,name='copyright_page'),
  path('terms_and_condition', cms_views.terms_and_condition,name='terms_and_condition'),  
  path('privacy_policy', cms_views.privacy_policy,name='privacy_policy'),
  path('software_license', cms_views.software_license,name='software_license'),
  path('location_information', cms_views.copyright_page,name='location_information'),

# Force Update
  path('force_update', force_update.force_update,name='force_update'),

# Vehicle information

  path('add_vehicle', vehicle_views.add_vehicle,name='add_vehicle'),
  path('vehicle_edit', vehicle_views.vehicle_edit,name='vehicle_edit'),
  path('vehicle_details', vehicle_views.vehicle_details,name='vehicle_details'),

# Add card
  path('add_card', payment_views.add_card,name='add_card'),
  path('card_details', payment_views.card_details,name='card_details'),
  path('card_delete', payment_views.card_delete,name='card_delete'),


# Update location

  path('update_location', auth_views.update_location,name='update_location'),


# Jobs 
  path('add_job', job_views.add_job,name='add_job'),
  path('job_list', job_views.job_list,name='job_list'),
  path('job_details', job_views.job_details,name='job_details'),
  path('remove_job', job_views.remove_job,name='remove_job'),

# Settings
  path('add_settings', setting.add_settings,name='add_settings'),
  path('setting_details', setting.setting_details,name='setting_details'),


]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
