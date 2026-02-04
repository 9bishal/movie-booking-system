web: gunicorn moviebooking.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 120 --workers 3
worker: celery -A moviebooking worker -l info --concurrency 2