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
	InStripe.create_invoice()
	return render(request,'Homepage/openup_homepage.html')

