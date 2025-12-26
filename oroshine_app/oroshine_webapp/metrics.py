"""
Optimized Prometheus metrics for Oroshine Django application
Only tracks essential business and application metrics
"""

from prometheus_client import Counter, Gauge, Histogram, REGISTRY, CollectorRegistry
from functools import wraps
import time

# Use a custom registry to have better control over metrics
custom_registry = CollectorRegistry()

# ============================================================================
# BUSINESS METRICS - Core KPIs for monitoring business health
# ============================================================================

appointment_bookings = Counter(
    'appointment_bookings_total',
    'Total appointment bookings',
    ['status', 'service'],
    registry=custom_registry
)

appointment_booking_failures = Counter(
    'appointment_booking_failures_total',
    'Failed appointment bookings',
    ['reason'],
    registry=custom_registry
)

email_send_total = Counter(
    'email_send_total',
    'Total emails sent',
    ['type', 'status'],
    registry=custom_registry
)

email_send_failures = Counter(
    'email_send_failures_total',
    'Failed email sends',
    ['type'],
    registry=custom_registry
)

calendar_event_total = Counter(
    'calendar_events_total',
    'Total calendar events created',
    ['status'],
    registry=custom_registry
)

calendar_event_failures = Counter(
    'calendar_event_failures_total',
    'Failed calendar event creations',
    registry=custom_registry
)

active_users = Gauge(
    'active_users_total',
    'Number of active users',
    registry=custom_registry
)

pending_appointments = Gauge(
    'pending_appointments_total',
    'Number of pending appointments',
    registry=custom_registry
)

# ============================================================================
# CELERY METRICS - Async task monitoring
# ============================================================================

celery_task_duration = Histogram(
    'celery_task_duration_seconds',
    'Time spent processing celery tasks',
    ['task_name'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
    registry=custom_registry
)

celery_task_total = Counter(
    'celery_task_total',
    'Total Celery tasks executed',
    ['task_name', 'status'],
    registry=custom_registry
)

# ============================================================================
# APPLICATION METRICS - Essential Django/HTTP metrics only
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=custom_registry
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0),
    registry=custom_registry
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
    registry=custom_registry
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def track_celery_task(task_name):
    """
    Decorator to track Celery task execution time and status
    
    Usage:
        @track_celery_task('send_email_task')
        def send_email_task(email):
            # task code
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'failure'
                raise
            finally:
                duration = time.time() - start_time
                celery_task_duration.labels(task_name=task_name).observe(duration)
                celery_task_total.labels(task_name=task_name, status=status).inc()
        return wrapper
    return decorator

def update_active_users_count(count):
    """Update the active users gauge"""
    active_users.set(count)

def update_pending_appointments_count(count):
    """Update the pending appointments gauge"""
    pending_appointments.set(count)

def track_appointment_booking(status, service):
    """Track appointment booking"""
    appointment_bookings.labels(status=status, service=service).inc()

def track_appointment_failure(reason):
    """Track appointment booking failure"""
    appointment_booking_failures.labels(reason=reason).inc()

def track_email_send(email_type, status):
    """Track email send"""
    email_send_total.labels(type=email_type, status=status).inc()

def track_email_failure(email_type):
    """Track email send failure"""
    email_send_failures.labels(type=email_type).inc()

def track_calendar_event(status):
    """Track calendar event creation"""
    calendar_event_total.labels(status=status).inc()

def track_calendar_failure():
    """Track calendar event creation failure"""
    calendar_event_failures.inc()

# ============================================================================
# DJANGO MIDDLEWARE FOR HTTP METRICS (Optional)
# ============================================================================

class PrometheusMetricsMiddleware:
    """
    Lightweight middleware to track HTTP requests
    Add to MIDDLEWARE in settings.py:
        'your_app.metrics.PrometheusMetricsMiddleware',
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Track metrics
        method = request.method
        endpoint = request.path or 'unknown'
        status = response.status_code
        
        # Simplify endpoint to avoid high cardinality
        # Group similar URLs together
        if '/api/' in endpoint:
            endpoint = '/api/*'
        elif '/static/' in endpoint:
            endpoint = '/static/*'
        elif '/media/' in endpoint:
            endpoint = '/media/*'
        
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        return response

# ============================================================================
# SCHEDULED METRICS UPDATE (for gauges)
# ============================================================================

def update_gauge_metrics():
    """
    Function to be called periodically (e.g., via Celery Beat)
    to update gauge metrics
    
    Example Celery Beat schedule:
    
    from celery.schedules import crontab
    
    CELERY_BEAT_SCHEDULE = {
        'update-metrics': {
            'task': 'your_app.tasks.update_metrics_task',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
        },
    }
    """
    from django.contrib.auth import get_user_model
    from your_app.models import Appointment  # Update with your model path
    
    User = get_user_model()
    
    # Update active users (users who logged in within last 15 minutes)
    from django.utils import timezone
    from datetime import timedelta
    
    fifteen_minutes_ago = timezone.now() - timedelta(minutes=15)
    active_count = User.objects.filter(last_login__gte=fifteen_minutes_ago).count()
    update_active_users_count(active_count)
    
    # Update pending appointments
    pending_count = Appointment.objects.filter(status='pending').count()
    update_pending_appointments_count(pending_count)

# ============================================================================
# EXAMPLE USAGE IN VIEWS/TASKS
# ============================================================================

"""
# In your views.py
from .metrics import track_appointment_booking, track_appointment_failure

def book_appointment(request):
    try:
        # ... booking logic ...
        track_appointment_booking(status='confirmed', service='consultation')
        return JsonResponse({'status': 'success'})
    except Exception as e:
        track_appointment_failure(reason='validation_error')
        return JsonResponse({'status': 'error'})

# In your tasks.py (Celery)
from .metrics import track_celery_task, track_email_send, track_email_failure

@track_celery_task('send_confirmation_email')
def send_confirmation_email(email_address, booking_id):
    try:
        # ... send email logic ...
        track_email_send(email_type='confirmation', status='sent')
    except Exception as e:
        track_email_failure(email_type='confirmation')
        raise

# Periodic task to update gauge metrics
@celery_app.task
def update_metrics_task():
    from .metrics import update_gauge_metrics
    update_gauge_metrics()
"""

# ============================================================================
# METRICS ENDPOINT VIEW
# ============================================================================

from django.http import HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

def prometheus_metrics(request):
    """
    Django view to expose Prometheus metrics
    
    Add to urls.py:
        path('metrics/', views.prometheus_metrics, name='prometheus-metrics'),
    """
    # Generate metrics from custom registry
    metrics_output = generate_latest(custom_registry)
    
    return HttpResponse(
        metrics_output,
        content_type=CONTENT_TYPE_LATEST
    )

# ============================================================================
# CONFIGURATION CHECK
# ============================================================================

def validate_metrics_setup():
    """
    Utility function to validate metrics are properly configured
    Call this during app startup or in management command
    """
    print("✅ Metrics Configuration Validation")
    print("-" * 50)
    
    # Check custom registry
    print(f"📊 Total metrics registered: {len(list(custom_registry.collect()))}")
    
    # List all metrics
    print("\n📋 Registered Metrics:")
    for family in custom_registry.collect():
        print(f"  - {family.name} ({family.type})")
    
    print("\n✅ Metrics setup validated successfully!")
    print("\n💡 Quick test:")
    print("   curl http://localhost:8000/metrics/")
    
if __name__ == '__main__':
    validate_metrics_setup()