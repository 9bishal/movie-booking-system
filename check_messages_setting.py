"""
Check the current MESSAGE_STORAGE setting
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moviebooking.settings')
django.setup()

from django.conf import settings

print("\n" + "="*60)
print("Current MESSAGE_STORAGE setting:")
print("="*60)
print(f"MESSAGE_STORAGE = {settings.MESSAGE_STORAGE}")
print("="*60 + "\n")
