from django.shortcuts import render
#  Import Serializer

# Create your views here.
from rest_framework.decorators import api_view


# Import token verifivations

from openup_api.master.auth_views import token_verification


# Import json response
from django.http import JsonResponse



# Generate links for cms 

@api_view(['POST'])
def cms_details(request,*args,**kwargs):

    # CHECK TOKEN VALUE
    token = request.data.get('token',None)

    check_user              =       token_verification(token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })  
    
    else:

        cms_links  =  {

            "Copyright"             :       "http://192.168.1.4:8000/api/copyright_page",
            "terms_and_condition"   :       "http://192.168.1.4:8000/api/terms_and_condition",
            "privacy_policy"        :       "http://192.168.1.4:8000/api/privacy_policy",
            "software_license"      :       "http://192.168.1.4:8000/api/software_license",
            "location_information"  :       "http://192.168.1.4:8000/api/location_information"

        }


        data =   {
            "cms"     :   cms_links
        }

        return JsonResponse({

        "status"    :       1,
        "message"   :       "Cms_Links provided",
        "data"      :       data
        })
    




# Render copyright page 


def copyright_page(request):
    return render(request,'CMS/copyright.html')



# Terms and Condition Page 

def terms_and_condition(request):
    return render(request,'CMS/terms_and_condition.html')


# Privacy Policy Page 

def privacy_policy(request):
    return render(request,'CMS/privacy_policy.html')


# Software License Page 


def software_license(request):
    return render(request,'CMS/software_license.html')



# Location Information Page 

def location_information(request):
    return render(request,'CMS/location_information.html')