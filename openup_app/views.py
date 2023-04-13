from django.shortcuts import render

 
# Create your views here.

from django.http import HttpResponse
import datetime
# import the logging library
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)


from openup.stripe import InStripe   
def openup_master(request): 
	return render('Homepage/openup_homepage.html')






def error_404(request,*args, **argv):
        data = {}
        return render(request,'error/404.html', data)
 

def error_500(request, *args, **argv):
        data = {}
        return render(request,'error/500.html', data)