from django.contrib import admin
from django.urls import path

from openup_api.master import auth_views, cms_views, force_update

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


]