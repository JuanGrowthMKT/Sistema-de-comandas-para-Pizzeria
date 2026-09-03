#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py seed_pizzas
python manage.py ensure_admin
python manage.py collectstatic --noinput
python manage.py backup_db
gunicorn config.wsgi:application --workers 1 --threads 4 --timeout 120