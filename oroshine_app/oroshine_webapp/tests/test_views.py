"""
Comprehensive tests for views
Run: python manage.py test oroshine_webapp.tests.test_views
"""

from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import json

from oroshine_webapp.models import (
    Appointment, Contact, UserProfile,
    DOCTOR_CHOICES, TIME_SLOTS
)


class AuthenticationViewsTest(TestCase):
    """Test authentication flows"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('custom_register')
        self.login_url = reverse('custom_login')
        self.logout_url = reverse('custom_logout')
        
    def tearDown(self):
        cache.clear()
        
    def test_register_get_page(self):
        """Test registration page loads"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        
    def test_register_valid_user(self):
        """Test successful user registration"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        response = self.client.post(self.register_url, data)
        
        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        
        # User should exist
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # Profile should be created
        user = User.objects.get(username='testuser')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        
        # User should be logged in
        self.assertTrue('_auth_user_id' in self.client.session)
        
    def test_register_duplicate_username(self):
        """Test registration with existing username"""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='Pass123!'
        )
        
        data = {
            'username': 'existing',
            'email': 'new@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        response = self.client.post(self.register_url, data)
        
        # Should show error
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'register_form', 'username', 
                           'A user with that username already exists.')
        
    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'register_form', 'password2',
                           "The two password fields didn't match.")
        
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(self.login_url, {
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)
        
    def test_login_ajax_valid(self):
        """Test AJAX login with valid credentials"""
        User.objects.create_user(
            username='testuser',
            password='TestPass123!'
        )
        
        response = self.client.post(
            self.login_url,
            {'username': 'testuser', 'password': 'TestPass123!'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('redirect_url', data)
        
    def test_login_ajax_invalid(self):
        """Test AJAX login with invalid credentials"""
        response = self.client.post(
            self.login_url,
            {'username': 'fake', 'password': 'fake'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        
    def test_logout(self):
        """Test logout functionality"""
        user = User.objects.create_user(username='test', password='pass')
        self.client.login(username='test', password='pass')
        
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse('_auth_user_id' in self.client.session)
        
    def test_rate_limiting_login(self):
        """Test rate limiting on login attempts"""
        for i in range(6):
            response = self.client.post(self.login_url, {
                'username': 'fake',
                'password': 'fake'
            })
            
        # 6th attempt should be rate limited
        self.assertEqual(response.status_code, 302)  # Redirects with error


class CheckAvailabilityTest(TestCase):
    """Test username/email availability checking"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('check_availability')
        User.objects.create_user(
            username='taken',
            email='taken@example.com',
            password='pass'
        )
        
    def test_username_available(self):
        """Test checking available username"""
        response = self.client.get(self.url, {'username': 'available'})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertFalse(data['is_taken'])
        
    def test_username_taken(self):
        """Test checking taken username"""
        response = self.client.get(self.url, {'username': 'taken'})
        data = json.loads(response.content)
        
        self.assertTrue(data['is_taken'])
        self.assertIn('suggestion', data)
        
    def test_email_taken(self):
        """Test checking taken email"""
        response = self.client.get(self.url, {'email': 'taken@example.com'})
        data = json.loads(response.content)
        
        self.assertTrue(data['is_taken'])
        
    def test_invalid_username_format(self):
        """Test invalid username format"""
        response = self.client.get(self.url, {'username': 'ab'})  # Too short
        data = json.loads(response.content)
        
        self.assertEqual(data['status'], 'error')
        self.assertTrue(data['is_taken'])


class PublicPagesTest(TestCase):
    """Test public pages accessibility"""
    
    def test_homepage_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        
    def test_about_page_loads(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        
    def test_service_page_loads(self):
        response = self.client.get(reverse('service'))
        self.assertEqual(response.status_code, 200)
        
    def test_team_page_loads(self):
        response = self.client.get(reverse('team'))
        self.assertEqual(response.status_code, 200)
        
    def test_price_page_loads(self):
        response = self.client.get(reverse('price'))
        self.assertEqual(response.status_code, 200)
        
    def test_testimonial_page_loads(self):
        response = self.client.get(reverse('testimonial'))
        self.assertEqual(response.status_code, 200)
        
    def test_contact_page_loads(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)


class AppointmentViewsTest(TransactionTestCase):
    """Test appointment booking system"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='TestPass123!'
        )
        self.profile = UserProfile.objects.create(user=self.user)
        self.client.login(username='patient', password='TestPass123!')
        
        self.appointment_url = reverse('appointment')
        self.check_slots_url = reverse('check_slots_ajax')
        
    def tearDown(self):
        cache.clear()
        
    def test_appointment_page_requires_login(self):
        """Test appointment page redirects when not logged in"""
        self.client.logout()
        response = self.client.get(self.appointment_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
    def test_appointment_page_loads_for_logged_in(self):
        """Test appointment page loads for authenticated users"""
        response = self.client.get(self.appointment_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment.html')
        
    def test_check_slots_ajax(self):
        """Test AJAX slot availability check"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        doctor_email = DOCTOR_CHOICES[0][0]
        
        response = self.client.post(
            self.check_slots_url,
            {
                'doctor_email': doctor_email,
                'date': tomorrow.isoformat()
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('slots', data)
        self.assertTrue(len(data['slots']) > 0)
        
    def test_check_slots_missing_params(self):
        """Test slot check with missing parameters"""
        response = self.client.post(self.check_slots_url, {})
        self.assertEqual(response.status_code, 400)
        
    def test_book_appointment_success(self):
        """Test successful appointment booking"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        data = {
            'name': 'Test Patient',
            'email': 'patient@example.com',
            'phone': '1234567890',
            'date': tomorrow.isoformat(),
            'time': TIME_SLOTS[0][0],
            'doctor_email': DOCTOR_CHOICES[0][0],
            'service': 'Consultation',
            'message': 'First visit'
        }
        
        response = self.client.post(
            self.appointment_url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('appointment_id', result)
        
        # Verify appointment was created
        appt = Appointment.objects.get(id=result['appointment_id'])
        self.assertEqual(appt.user, self.user)
        self.assertEqual(appt.status, 'pending')
        
    def test_book_appointment_duplicate_slot(self):
        """Test booking already taken slot"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        time_slot = TIME_SLOTS[0][0]
        doctor = Doctor[0][0]
        
        # Create existing appointment
        Appointment.objects.create(
            user=self.user,
            name='First Patient',
            email='first@example.com',
            date=tomorrow,
            time=time_slot,
            doctor_email=doctor,
            service='Consultation',
            status='confirmed'
        )
        
        # Try to book same slot
        data = {
            'name': 'Second Patient',
            'email': 'second@example.com',
            'date': tomorrow.isoformat(),
            'time': time_slot,
            'doctor_email': doctor,
            'service': 'Consultation',
        }
        
        response = self.client.post(
            self.appointment_url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 409)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
    def test_book_appointment_invalid_data(self):
        """Test booking with invalid data"""
        response = self.client.post(
            self.appointment_url,
            {'name': 'Test'},  # Missing required fields
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)


class UserProfileViewsTest(TestCase):
    """Test user profile functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.profile = UserProfile.objects.create(user=self.user)
        self.client.login(username='testuser', password='TestPass123!')
        self.url = reverse('user_profile')
        
    def test_profile_requires_login(self):
        """Test profile page requires authentication"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        
    def test_profile_loads(self):
        """Test profile page loads"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        
    def test_profile_update(self):
        """Test updating profile"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'phone': '9876543210',
            'city': 'Mumbai',
            'state': 'Maharashtra',
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        
        # Verify update
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, '9876543210')


class ContactViewTest(TestCase):
    """Test contact form"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='pass'
        )
        self.url = reverse('contact')
        
    def test_contact_page_loads(self):
        """Test contact page loads"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
    def test_contact_requires_login(self):
        """Test contact submission requires login"""
        response = self.client.post(self.url, {
            'name': 'Test',
            'email': 'test@example.com',
            'subject': 'Question',
            'message': 'Test message'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
    def test_contact_submission_success(self):
        """Test successful contact form submission"""
        self.client.login(username='test', password='pass')
        
        response = self.client.post(self.url, {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Inquiry',
            'message': 'I have a question'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Verify contact was created
        self.assertTrue(Contact.objects.filter(user=self.user).exists())


class CacheTest(TestCase):
    """Test caching functionality"""
    
    def setUp(self):
        cache.clear()
        
    def tearDown(self):
        cache.clear()
        
    def test_homepage_stats_cached(self):
        """Test homepage stats are cached"""
        response1 = self.client.get(reverse('home'))
        response2 = self.client.get(reverse('home'))
        
        # Both should succeed
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Second request should hit cache
        self.assertIsNotNone(cache.get('homepage_stats'))
        
    def test_slot_availability_cached(self):
        """Test slot availability is cached"""
        user = User.objects.create_user(username='test', password='pass')
        client = Client()
        client.login(username='test', password='pass')
        
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        doctor = DOCTOR_CHOICES[0][0]
        
        # First request
        response1 = client.post(reverse('check_slots_ajax'), {
            'doctor_email': doctor,
            'date': tomorrow.isoformat()
        })
        
        # Check cache
        cache_key = f"slots:{doctor}:{tomorrow}"
        self.assertIsNotNone(cache.get(cache_key))