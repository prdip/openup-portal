from django.urls import path,re_path
from django.conf import settings
from django.conf.urls.static import static
from openup_api.views import auth_views, cms_views, force_update,vehicle_views,payment_views,job_views,feedback_views,location_views, paypal_views, apple_pay as apple_pay_views, venmo_views
from openup_api.views import usersetting
from django.urls import reverse
from django.views.static import serve

from openup_api.views import paypal_views

urlpatterns = [

# User Authentication 
  path('registration', auth_views.user_register,name='registration'),
  path('login', auth_views.login,name='login'),
  path('logout', auth_views.logout,name='logout'),
  path('delete_account', auth_views.delete_account,name='delete_account'),
  path('user_details', auth_views.get_user_details,name='user-details'),
    
  # Account confirm or verify user 
  path('confirm_account/<slug:token>', auth_views.confirm_account,name='confirm_account'),
  path('activate', auth_views.activate_account,name='activate'),
  path('verify-account/<slug:token>', auth_views.verify_account,name='verify_account'),
  path('verify-client', auth_views.verify_client,name='verify_client'),
 
# UPDATE
  path('email_update', auth_views.email_update,name='email-update'),


# Forget Password
  path('change_password', auth_views.change_password,name='change_password'),
  path('forget_password', auth_views.forget_password,name='forget_password'),
  path('reset_password/<slug:token>', auth_views.reset_password,name='reset_password'),
 
# CMS LINKS
  path('cms_details', cms_views.cms_details,name='cms_details'),

#  CMS PAGES
  path('privacy_policy', cms_views.privacy_policy,name='privacy_policy'),

  path('copyright_page', cms_views.copyright_page,name='copyright_page'),
  path('terms_and_condition', cms_views.terms_and_condition,name='terms_and_condition'),  
  path('software_license', cms_views.software_license,name='software_license'),
  path('location_information', cms_views.copyright_page,name='location_information'),

# Force Update
  path('force_update', force_update.force_update,name='force_update'),


# Vehicle information
  path('add_vehicle', vehicle_views.add_vehicle,name='add_vehicle'),
  path('vehicle_edit', vehicle_views.vehicle_edit,name='vehicle_edit'),
  path('vehicle_details', vehicle_views.vehicle_details,name='vehicle_details'),


# Add Payment
  path('add_card', payment_views.add_card,name='add_card'),
  path('card_details', payment_views.card_details,name='card_details'),
   
# Create customer using stripe
  path('create-customer', payment_views.create_customer,name='create_customer'),
  path('link-payment', payment_views.link_payment_method,name='link_payment'),
  path('ask-for-payment', payment_views.ask_for_payment,name='ask_for_payment'),

  # Manual payment from job list
  path('manual-payment', payment_views.manual_payment,name='manual_payment'),
  path('manual-payment-success', payment_views.manual_payment_success,name='manual_payment_success'),

# Update location
  path('update_location', location_views.update_location,name='update_location'),
  path('service_available', location_views.service_available,name='service_available'),
  path('distance-calculation', location_views.dist_calculation,name='distance_calculation'),
  path('employee-location', location_views.employee_location,name='employee-location'),
  
  


# Jobs 
  path('add_job', job_views.add_job,name='add_job'),
  path('job_details', job_views.job_details,name='job_details'),
  path('remove_job', job_views.remove_job,name='remove_job'),
  path('job_accept', job_views.accept_job,name='job_accept'),
  path('complete_job', job_views.complete_job,name='complete_job'),
  path('reject_job', job_views.reject_job,name='reject_job'),
  path('cancel-job', job_views.cancel_job,name='cancel_job'),
  path('upload-images', job_views.upload_images,name='upload-images'),
  path('get-upload-images', job_views.getuploaded_image,name='get-upload-images'),



  path('cancel-job-by-emp', job_views.cancel_job_by_employee,name='cancel_job_by_employee'),



# Job list of client
  path('client-joblist', job_views.client_joblist,name='client_joblist'),
# Job list of employee
  path('employee-joblist', job_views.employee_joblist,name='employee_joblist'),
# Current job session (restore after the app is closed/reopened)
  path('active-job', job_views.active_job,name='active_job'),

# Settings
  path('add_settings', usersetting.add_settings,name='add_settings'),
  path('setting-details', usersetting.setting_details,name='setting_details'),


# Feedback
  path('add_feedback', feedback_views.add_feedback,name='add_feedback'),



# create_customer
  # First Payment with paypal
  path('create-paypal-customer', paypal_views.create_customer,name='create_customer'),
  # Recurring Payment
  path('paypal-payment', paypal_views.paypal_payment,name='paypal_payment'),

  #Check customer is stripe cust or paypal cust 
  path('payment-type', paypal_views.add_payment_type,name='payment_type'),



  path('paypal-payment-token-receiver', paypal_views.paypal_payment_token_receiver,name='paypal_payment_token_receiver'),
  


  path('apple-pay', apple_pay_views.apple_pay,name='apple_pay'),

# Venmo (via paypal) - two step because the buyer approves in the venmo app
  path('venmo-setup', venmo_views.venmo_setup,name='venmo_setup'),
  path('venmo-confirm', venmo_views.venmo_confirm,name='venmo_confirm'),
  




  # webhook urls  
  path('create-webhook', paypal_views.create_webhook,name='create_webhook'),
  path('webhook-data', paypal_views.receive_webhook_data, name='webhook_data'),


  path('create-paypal-token', paypal_views.create_paypal_token, name='create_paypal_token'),

 
  
# Employee active inactive
  path('employee-status', auth_views.employee_status,name='employee_status'),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),

    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
  
  
  path('privacy_policy', cms_views.privacy_policy,name='privacy_policy'),
 
  


 
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

 