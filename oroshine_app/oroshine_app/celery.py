import os
from celery import Celery
from celery.schedules import crontab

from celery.signals import (
    task_prerun, task_postrun, 
    task_failure, worker_ready
)

import time
from oroshine_webapp.metrics import celery_task_total, celery_task_duration 



# Correct Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oroshine_app.settings')

# Create Celery app
app = Celery('oroshine_app')

# Load config from Django settings (CELERY_ prefix)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Explicitly autodiscover tasks in your apps
app.autodiscover_tasks(['oroshine_webapp'])

# Periodic tasks
app.conf.beat_schedule = {
    'check-appointment-reminders-hourly': {
        'task': 'oroshine_webapp.tasks.check_and_send_reminders',
        'schedule': crontab(minute=0),
    },
    'cleanup-old-cache-daily': {
        'task': 'oroshine_webapp.tasks.cleanup_old_cache',
        'schedule': crontab(hour=2, minute=0),
    },
}

# Task defaults
app.conf.update(
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=30,
    task_max_retries=3,
)





# Start Prometheus exporter
@worker_ready.connect
def setup_prometheus_exporter(sender, **kwargs):
    start_http_server(9808)

@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    task.start_time = time.time()

@task_postrun.connect
def task_postrun_handler(task_id, task, *args, **kwargs):
    if hasattr(task, 'start_time'):
        duration = time.time() - task.start_time
        celery_task_duration.labels(task_name=task.name).observe(duration)
    celery_task_total.labels(task_name=task.name, status='success').inc()

@task_failure.connect
def task_failure_handler(task_id, exception, *args, **kwargs):
    celery_task_total.labels(task_name=kwargs.get('sender').name, status='failure').inc()




@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


