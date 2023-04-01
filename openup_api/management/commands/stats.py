from django.core.management.base import BaseCommand

# IMPORT BACKGROUND PAYMENTS
from openup_api.views.job_views import background_payment 
 
# Import Queryset
from django.db.models import Q

# Import Models here
from openup_app.models import PaymentFailedInfo,Jobs
'''To create custom command class inherits basecommand '''

class Command(BaseCommand):

        def handle(self, *args, **kwargs):
                help       =    'payment in background after payment fails'           
                failed_job =    PaymentFailedInfo.objects.all()

                for pay_id in failed_job:
                        try:
                            job_records = Jobs.objects.exclude(Q(is_delete=1) and Q(job_pay_status=1)).get(job_id=pay_id.job_id)

                        except:
                            job_records=None

                        if job_records != None and job_records.job_pay_status == 0:
                                user_id =   job_records.user.user_id
                                job_id  =    job_records.job_id
                                background_payment.delay(user_id,job_id)


                return help
 