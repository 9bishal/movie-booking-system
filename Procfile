web: gunicorn moviebooking.wsgi:application --timeout 120 --workers 3
worker: celery -A moviebooking worker --loglevel=info
beat: celery -A moviebooking beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
