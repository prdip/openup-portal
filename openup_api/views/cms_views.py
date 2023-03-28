from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view

# Import json response
from django.http import JsonResponse



# Generate links for cms 

@api_view(['POST'])
def cms_details(request,*args,**kwargs):
        

        # return cms links as a response
        cms_links  =  {

            "copyright"             :       "http://192.168.1.2:8000/api/copyright_page",
            "terms_and_condition"   :       "http://192.168.1.2:8000/api/terms_and_condition",
            "privacy_policy"        :       "http://192.168.1.2:8000/api/privacy_policy",
            "software_license"      :       "http://192.168.1.2:8000/api/software_license",
            "location_information"  :       "http://192.168.1.2:8000/api/location_information"

        }


        data =   {
            "cms"     :   cms_links
        }

        return JsonResponse({

        "success"    :       1,
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