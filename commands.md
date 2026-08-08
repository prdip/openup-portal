python manage.py runserver 192.168.1.10:8001


python manage.py makemigrations

python manage.py migrate


pip freeze > requirements.txt

pip install -r requirements.txt


celery -A openup.celery worker -l INFO


## Celery worker

All notifications run on the worker above. It must be running, otherwise tasks
queue in Redis and no push is delivered.

Check what the running worker knows about:

    celery -A openup.celery inspect registered
    celery -A openup.celery inspect active

On a server, do not start it by hand - install the systemd unit so it restarts
itself (see `deploy/celery-worker.service`):

    sudo cp deploy/celery-worker.service /etc/systemd/system/openup-celery.service
    sudo systemctl daemon-reload
    sudo systemctl enable --now openup-celery
    sudo systemctl status openup-celery

To develop without a worker or Redis at all, run tasks inline by putting this in
`.env` (leave it out/False anywhere a worker runs):

    CELERY_TASK_ALWAYS_EAGER=True
