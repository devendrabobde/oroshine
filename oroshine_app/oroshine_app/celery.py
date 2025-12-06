"""
Celery configuration for oroshine_app project
Place this file in your main project directory (same level as settings.py)
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oroshine_app.settings')

# Create Celery app
app = Celery('oroshine_app')

# Load configuration from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'check-appointment-reminders-hourly': {
        'task': 'oroshine_webapp.tasks.check_and_send_reminders',
        'schedule': crontab(minute=0),  # Every hour
    },
    'cleanup-old-cache-daily': {
        'task': 'oroshine_webapp.tasks.cleanup_old_cache',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}

# Task configuration
app.conf.update(
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=30,  # 30 seconds
    task_max_retries=3,
)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')