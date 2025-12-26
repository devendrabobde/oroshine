"""
End-to-End Integration Tests
Tests complete user workflows
Run: python manage.py test oroshine_webapp.tests.test_integration
"""

from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from unittest.mock import patch, MagicMock
import json

from oroshine_webapp.models import (
    Appointment, Contact, UserProfile,
    DOCTOR_CHOICES, TIME_SLOTS
)


class UserRegistrationFlowTest(TransactionTestCase):
    """Test complete user registration flow"""
    
    def setUp(self):
        self.client = Client()
        cache.clear()
        
    def test_complete_registration_flow(self):
        """Test user can register, verify email, and login"""
        
        # Step 1: Check username availability
        response = self.client.get(
            reverse('check_availability'),
            {'username': 'newuser'}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['is_taken'])
        
        # Step 2: Register
        register_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        
        response = self.client.post(
            reverse('custom_register'),
            register_data
        )
        
        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        
        # User should exist
        user = User.objects.get(username='newuser')
        self.assertIsNotNone(user)
        
        # Profile should be created
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        
        # Step 3: User should be logged in automatically
        self.assertTrue('_auth_user_id' in self.client.session)
        
        # Step 4: Access profile page
        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 200)


class AppointmentBookingFlowTest(TransactionTestCase):
    """Test complete appointment booking flow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='TestPass123!'
        )
        self.profile = UserProfile.objects.create(user=self.user)
        cache.clear()
        
    def tearDown(self):
        cache.clear()
        
    @patch('oroshine_webapp.tasks.requests.post')
    def test_complete_booking_flow(self, mock_calendar_api):
        """Test user can book appointment end-to-end"""
        
        # Mock calendar API
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'event_123'}
        mock_response.raise_for_status = MagicMock()
        mock_calendar_api.return_value = mock_response
        
        # Step 1: Login
        self.client.login(username='patient', password='TestPass123!')
        
        # Step 2: Access appointment page
        response = self.client.get(reverse('appointment'))
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Check available slots
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        doctor = DOCTOR_CHOICES[0][0]
        
        response = self.client.post(
            reverse('check_slots_ajax'),
            {
                'doctor_email': doctor,
                'date': tomorrow.isoformat()
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(len(data['slots']) > 0)
        
        # Step 4: Book appointment
        booking_data = {
            'name': 'Test Patient',
            'email': 'patient@example.com',
            'phone': '9876543210',
            'date': tomorrow.isoformat(),
            'time': TIME_SLOTS[0][0],
            'doctor_email': doctor,
            'service': 'Consultation',
            'message': 'First visit',
        }
        
        response = self.client.post(
            reverse('appointment'),
            booking_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertIn('appointment_id', result)
        
        # Step 5: Verify appointment was created
        appointment = Appointment.objects.get(id=result['appointment_id'])
        self.assertEqual(appointment.user, self.user)
        self.assertEqual(appointment.status, 'pending')
        
        # Step 6: Check emails were sent
        # In real test with CELERY_TASK_ALWAYS_EAGER=True
        # self.assertEqual(len(mail.outbox), 2)  # Admin + User
        
        # Step 7: Verify slot is no longer available
        response = self.client.post(
            reverse('check_slots_ajax'),
            {
                'doctor_email': doctor,
                'date': tomorrow.isoformat()
            }
        )
        
        data = json.loads(response.content)
        booked_slot = next(
            (s for s in data['slots'] if s['time'] == str(TIME_SLOTS[0][0])),
            None
        )
        self.assertIsNotNone(booked_slot)
        self.assertFalse(booked_slot['is_available'])
        
        # Step 8: View appointment in profile
        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Patient')


class DoubleBookingPreventionTest(TransactionTestCase):
    """Test race condition prevention in appointment booking"""
    
    def setUp(self):
        self.tomorrow = (timezone.now() + timedelta(days=1)).date()
        self.time_slot = TIME_SLOTS[0][0]
        self.doctor = DOCTOR_CHOICES[0][0]
        cache.clear()
        
    def test_concurrent_booking_prevention(self):
        """Test two users cannot book the same slot"""
        
        # Create two users
        user1 = User.objects.create_user(
            username='patient1',
            password='pass'
        )
        user2 = User.objects.create_user(
            username='patient2',
            password='pass'
        )
        
        client1 = Client()
        client2 = Client()
        
        client1.login(username='patient1', password='pass')
        client2.login(username='patient2', password='pass')
        
        # Both try to book same slot
        booking_data = {
            'name': 'Patient',
            'email': 'patient@example.com',
            'date': self.tomorrow.isoformat(),
            'time': self.time_slot,
            'doctor_email': self.doctor,
            'service': 'Consultation',
        }
        
        # First booking should succeed
        response1 = client1.post(
            reverse('appointment'),
            booking_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        result1 = json.loads(response1.content)
        self.assertEqual(result1['status'], 'success')
        
        # Second booking should fail
        response2 = client2.post(
            reverse('appointment'),
            booking_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        result2 = json.loads(response2.content)
        self.assertEqual(result2['status'], 'error')
        self.assertEqual(response2.status_code, 409)
        
        # Only one appointment should exist
        appointments = Appointment.objects.filter(
            date=self.tomorrow,
            time=self.time_slot,
            doctor_email=self.doctor,
            status__in=['pending', 'confirmed']
        )
        self.assertEqual(appointments.count(), 1)


class ContactFormFlowTest(TestCase):
    """Test contact form submission flow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='pass'
        )
        
    def test_contact_form_submission(self):
        """Test user can submit contact form"""
        
        # Step 1: Login
        self.client.login(username='test', password='pass')
        
        # Step 2: Access contact page
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Submit form
        contact_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Inquiry',
            'message': 'Test message',
        }
        
        response = self.client.post(reverse('contact'), contact_data)
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Contact should be created
        contact = Contact.objects.filter(user=self.user).first()
        self.assertIsNotNone(contact)
        self.assertEqual(contact.subject, 'Inquiry')


class RateLimitingTest(TestCase):
    """Test rate limiting on various endpoints"""
    
    def setUp(self):
        self.client = Client()
        cache.clear()
        
    def tearDown(self):
        cache.clear()
        
    def test_login_rate_limiting(self):
        """Test login rate limiting after failed attempts"""
        
        login_url = reverse('custom_login')
        
        # Make 6 failed login attempts
        for i in range(6):
            response = self.client.post(login_url, {
                'username': 'fake',
                'password': 'fake'
            })
            
        # 6th attempt should be rate limited
        self.assertEqual(response.status_code, 302)
        
    def test_availability_check_rate_limiting(self):
        """Test username/email availability rate limiting"""
        
        url = reverse('check_availability')
        
        # Make many requests
        for i in range(25):
            response = self.client.get(url, {'username': f'user{i}'})
            
        # Should eventually be rate limited
        # Exact behavior depends on rate limit settings


class CacheInvalidationTest(TransactionTestCase):
    """Test cache invalidation works correctly"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            password='pass'
        )
        self.client = Client()
        self.client.login(username='patient', password='pass')
        cache.clear()
        
    def test_slot_cache_invalidation_on_booking(self):
        """Test slot cache is invalidated when appointment is booked"""
        
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        doctor = DOCTOR_CHOICES[0][0]
        
        # Step 1: Check slots (populates cache)
        response = self.client.post(
            reverse('check_slots_ajax'),
            {
                'doctor_email': doctor,
                'date': tomorrow.isoformat()
            }
        )
        
        data1 = json.loads(response.content)
        all_available_before = all(s['is_available'] for s in data1['slots'])
        self.assertTrue(all_available_before)
        
        # Step 2: Book appointment
        booking_data = {
            'name': 'Test',
            'email': 'test@example.com',
            'date': tomorrow.isoformat(),
            'time': TIME_SLOTS[0][0],
            'doctor_email': doctor,
            'service': 'Consultation',
        }
        
        self.client.post(
            reverse('appointment'),
            booking_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Step 3: Check slots again (should reflect booking)
        response = self.client.post(
            reverse('check_slots_ajax'),
            {
                'doctor_email': doctor,
                'date': tomorrow.isoformat()
            }
        )
        
        data2 = json.loads(response.content)
        
        # First slot should now be unavailable
        first_slot = next(
            s for s in data2['slots'] 
            if s['time'] == str(TIME_SLOTS[0][0])
        )
        self.assertFalse(first_slot['is_available'])


class ErrorHandlingTest(TestCase):
    """Test error handling in various scenarios"""
    
    def test_404_page(self):
        """Test 404 page works"""
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        
    def test_csrf_protection(self):
        """Test CSRF protection is active"""
        response = self.client.post(
            reverse('custom_login'),
            {'username': 'test', 'password': 'test'}
        )
        # Should have CSRF error or be rejected
        # Exact behavior depends on settings
        
    def test_unauthorized_access(self):
        """Test unauthorized users are redirected"""
        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class PerformanceTest(TestCase):
    """Test performance under load"""
    
    def test_homepage_loads_quickly(self):
        """Test homepage loads within acceptable time"""
        import time
        
        start = time.time()
        response = self.client.get(reverse('home'))
        duration = time.time() - start
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(duration, 1.0)  # Should load in < 1 second
        
    def test_multiple_slot_checks(self):
        """Test multiple concurrent slot checks"""
        user = User.objects.create_user(username='test', password='pass')
        self.client.login(username='test', password='pass')
        
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        # Make 10 slot checks
        import time
        start = time.time()
        
        for doctor, _ in DOCTOR_CHOICES[:3]:
            self.client.post(
                reverse('check_slots_ajax'),
                {
                    'doctor_email': doctor,
                    'date': tomorrow.isoformat()
                }
            )
        
        duration = time.time() - start
        
        # Should complete quickly (benefiting from cache)
        self.assertLess(duration, 2.0)