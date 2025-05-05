#!/bin/bash

set -e
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py crontab add

# Start Gunicorn
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000