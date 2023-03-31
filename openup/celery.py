# django_db_task/celery.py

import os
from celery import Celery
from django.conf import settings
from celery.signals import setup_logging

@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)


os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE', 
    'openup.settings'
)


app = Celery('openup')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()



@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))