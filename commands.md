python manage.py runserver 192.168.1.10:8001


python manage.py makemigrations

python manage.py migrate


pip freeze > requirements.txt

pip install -r requirements.txt


celery -A openup.celery worker -l INFO
