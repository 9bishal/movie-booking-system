"""
❓ WHY THIS FILE EXISTS:
Linking the Celery app in __init__.py ensures that when Django starts, 
the Celery app is loaded so that @shared_task annotations work properly.
"""
from .celery import app as celery_app
__all__ = ('celery_app',)
