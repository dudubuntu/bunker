#!/bin/bash

python manage.py makemigrations --no-input

python manage.py makemigrations web --no-input

python manage.py migrate --no-input

python manage.py migrate web --no-input

python manage.py createsuperuser --no-input

exec gunicorn bunker_proj.wsgi:application -b 0.0.0.0:8000 --reload