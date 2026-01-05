"""
❓ WHY THIS FILE EXISTS:
This is the core configuration for Celery. It tells Celery how to find its settings 
in Django, how to discover background tasks, and defines the 'Beat' schedule 
for recurring tasks (like cleaning up expired bookings).
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')

app = Celery('moviebooking')
# ⚙️ HOW: Tell Celery where settings are
app.config_from_object('django.conf:settings', namespace='CELERY')

# 🔍 WHY: Autodiscover tasks
# Celery will look for a file named 'tasks.py' in every installed app automatically.
app.autodiscover_tasks()

# 📧 Manually import email tasks since they're in email_utils.py, not tasks.py
# This ensures Celery recognizes all @shared_task decorated functions
from bookings import email_utils  # noqa: F401

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Add this after app.config_from_object
app.conf.beat_schedule = {
    'release-expired-bookings-every-minute': {
        'task': 'bookings.tasks.release_expired_bookings',
        'schedule': 60.0,  # Every minute
    },
    'send-showtime-reminders-every-hour': {
        'task': 'bookings.tasks.send_showtime_reminders',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-data-daily': {
        'task': 'bookings.tasks.cleanup_old_data',
        'schedule': 86400.0,  # Daily
    },
}