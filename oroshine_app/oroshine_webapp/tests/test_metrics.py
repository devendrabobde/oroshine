# example but changes needed  not for prod 
from django.test import TestCase, Client
from .tasks import send_appointment_email_task
from django.core.cache import cache
from datetime import datetime, timedelta
from .models import Appointment, UserProfile, User

class MetricsAndTasksTestCase(TestCase):
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(username="testuser", email="test@test.com")
        self.client = Client()
        
        # Create a test appointment
        self.appointment = Appointment.objects.create(
            user=self.user,
            date=datetime.now().date(),
            time=(datetime.now() + timedelta(hours=1)).time(),
            service="dental",
            status="pending",
        )
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint"""
        response = self.client.get("/metrics/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"appointment_bookings_total", response.content)
    
    def test_send_appointment_email_task(self):
        """Test sending an appointment email task"""
        result = send_appointment_email_task(self.appointment.id)
        self.assertIn(result['status'], ['success', 'skipped'])
    
    def test_cache_rate_limit(self):
        """Test rate limit helper functions"""
        cache_key = f"rate_limit:test"
        cache.set(cache_key, 0)
        self.assertEqual(cache.get(cache_key), 0)
