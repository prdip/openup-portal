from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
import datetime
# import the logging library
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)



def hello_reader(request):
    logger.error('ERRROR HAPPENED '+str(datetime.datetime.now())+' hours!')
    logger.warning('WARNING HAPPENED '+str(datetime.datetime.now())+' hours!')
    return HttpResponse("<h1>Hello FreeCodeCamp.org Reader :)</h1>")