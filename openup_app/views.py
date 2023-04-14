from django.shortcuts import render,redirect
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from openup_app.models import Registration,Session
from django.http.response import JsonResponse,HttpResponse
from django.contrib import messages
import secrets
import datetime
from django.contrib.auth.hashers import make_password, check_password
# Create your views here.

from openup_api.views.validation import password_validation



from django.http import HttpResponse
import datetime
# import the logging library
import logging
# Get an instance of a logger
logger = logging.getLogger(__file__)


from openup.stripe import InStripe   
def openup_master(request): 
        return render(request,'Homepage/openup_homepage.html')






def error_404(request,*args, **argv):
        data = {}
        return render(request,'error/404.html', data)
 

def error_500(request, *args, **argv):
        data = {}
        return render(request,'error/500.html', data)





def error_log(request):
        try:
                session_token = request.session['session_key']
        except:
                session_token = None
        if session_token ==None:
                return redirect('admin_login')
        try:
                check_user = Session.objects.filter(session_token=session_token).values('session_user').first()['session_user']
        
        except:
                check_user = None

        user = Registration.objects.get(user_id = check_user)
        
        if user.user_email != "admin@gmail.com":
                 return redirect('admin_login')
        

     
        return render(request,'error/error_log.html')

def error_list(request):
        try:    
                mylines = []   
                with open("debug_logs", "rt") as myfile:
                        lines = myfile.read().split('INFO')
                        
                       
                        # for myline in myfile:                # For each line, stored as myline,
                        #         mylines.append(myline) 
        except:
                pass
   
         
        # page = request.GET.get('page',1)
        
        # # if page == 1:   
        # #         paginator  = Paginator(lines,3)
        # # else:       
        # #         paginator  = Paginator(lines, 2)  #
        # paginator  = Paginator(lines,3)
        # try:
        #         line = paginator.get_page(page)  # returns the desired page object
        # except PageNotAnInteger:   # if page_number is not an integer then assign the first page
        #         line = paginator.page(1)
        # except EmptyPage:
        
        #         line = paginator.page(paginator.num_pages)
        
        # context = {'page_obj': line}
        count = 10
        all_records      = {
                        "recordsTotal"      :   count,      #Total no of records in the database
                        "recordsFiltered"   :   count,      #Mandatory data for the datatable
                        "data"              :   lines,    
                                }

        return JsonResponse(all_records,safe=False,content_type = "application/json")


def admin_login(request):
        return render(request,'Authentication/login.html')


def do_login(request):
        if request.method=="POST":
                email = request.POST['email']
                password = request.POST['password']
                try:
                        check = Registration.objects.filter(user_email=email).values('user_password','user_id').first()
                except:
                        check = None
                
               
                
                check_pass = check_password(password,check['user_password'])
                if check is None:
                        messages.warning(request,"Invalid user type")
                        return JsonResponse({
                                "status":400,
                                "message":"user not found"
                        })
                if check_pass == False :
                        return JsonResponse({
                                "status":400,
                                "message":"password does not match"
                        })
                session_token =         secrets.token_hex()
                exp_time      =         datetime.datetime.now()+ datetime.timedelta(days=30)
                user          =         Registration.objects.get(user_id=int(check['user_id']))
           

                session = Session(

                session_user              =         user,
                session_user_email        =        user.user_email,
                session_token             =        session_token,
                session_exp               =        exp_time,
                session_status            =        True, #login
                session_created_at        =        datetime.datetime.now(),
                session_is_delete         =        False                  
                )
                request.session['session_key'] = session_token
                session.save()
                return JsonResponse({
                                "status":200,
                                "message":"login success"
                        })
        



def admin_logout(request):
        session_token = request.session['session_key']
        try:
                check_user = Session.objects.filter(session_token=session_token).values('session_id').first()['session_id']
        
        except:
                check_user = None

        if check_user == None:
                return redirect('admin_login')
        session = Session.objects.get(session_id=check_user)

        update_data = {
                "session_is_delete"     :       1
        }
        del request.session['session_key']

        session.update(**update_data)

        return redirect('admin_login')

