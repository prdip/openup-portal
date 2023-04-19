# Create your views here.
from rest_framework.decorators import api_view

# import Json Response
from django.http.response import JsonResponse

# Import token verifications
from openup_api.views.auth_views import token_verification

# import datetime
import datetime

# Import Q
from django.db.models import Q

# Import Models here
from openup_app.models import Feedback,Jobs

# Import Serializer
from openup_app.serializers import FeedbackSerializer



'''FEEDBACK  VIEWS'''


'''ADD FEEDBACK API
FOR ONE JOB ONE FEEDBACK WILL ADDED
'''


@api_view(['POST'])
def add_feedback(request):
  
    token = request.headers['Authorization']
    user_token = token.replace("Bearer",'')  
    check_user      =       token_verification(user_token)

    if check_user is None:
        return JsonResponse({
                "success"     :   0,
                "message"     :   "Unauthorized User",
        })
    
    # if token verified
    else:
        # required data
        user_id             =   check_user['session_user']
        job_id              =   request.data.get('job_id',None)
        feedback_star       =   request.data.get('feedback_star',None)
        feedback_comment    =   request.data.get('feedback_comment',None)

        try:
            check_feedback  =   Feedback.objects.filter(feedback_job=job_id).exists()
        except:
            check_feedback  =   False
        
        #  if feedback is already exist
        if check_feedback:
            return JsonResponse({
                "success"    :   0,
                "message"   :   "Feedback already exist"
            })

        #  check required data

        if feedback_star is None or feedback_comment is None:
            return JsonResponse({
                "success"    :   0,
                "message"   :   "please provide data"
            })

        # try to found job id found 
        try:
            job_record      =       Jobs.objects.exclude(Q(is_delete=1) and Q(job_status_id=1)).get(job_id=job_id)
        except:
            job_record      =       None

        # if job does not exist
        if job_record is None:
            return JsonResponse({
                "success"    :       0,
                "message"   :   "please provide job id"
            })
        
        # if job is not user job 
        
        if job_record.user_id != user_id:
            return JsonResponse({
                "success"    :   0,
                "message"   :   "please provide valid job id"
            })
        
        # FEEDBACK DATA

        feedback_data   =   {
            "feedback_job"     :       job_record.job_id,
            "feedback_user"    :       job_record.user.user_id,
            "feedback_stars"   :       feedback_star,
            "feedback_comment" :       feedback_comment,
            "created_at"       :       datetime.datetime.now()
        }

        # FEEDBACK SERIALIZER
        feedback_ser    =       FeedbackSerializer(data=feedback_data)
        if feedback_ser.is_valid():
            feedback_ser.save()
            return JsonResponse({
                "success"    :   1,
                "message"   :   "Feedback saved successfully"
                })
        else:
             return JsonResponse({
                "success"    :   0,
                "message"   :   "error occured"
                })




       
