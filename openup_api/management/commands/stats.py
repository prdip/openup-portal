from django.core.management.base import BaseCommand
from openup_api.views.job_views import background_payment 
 

'''To create custom command class inherits basecommand '''

class Command(BaseCommand):
        def add_arguments(self, parser):
                parser.add_argument('user_id', nargs='+', type=int, help='User ID')
                parser.add_argument('job_id', nargs='+', type=int, help='Job ID')


        def handle(self, *args, **kwargs):
            help = 'payment in background after payment fails'           
            user_id = kwargs['user_id'][0]
            job_id  = kwargs['job_id'][0]
            background_payment.delay(user_id,job_id)
            return help