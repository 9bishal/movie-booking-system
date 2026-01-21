web: gunicorn moviebooking.wsgi:application --timeout 120 --workers 2
# worker and beat disabled on Railway free tier to save memory
# worker: celery -A moviebooking worker --loglevel=info
# beat: celery -A moviebooking beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
