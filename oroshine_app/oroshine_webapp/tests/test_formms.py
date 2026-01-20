"""
Comprehensive tests for forms
Run: python manage.py test oroshine_webapp.tests.test_forms
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from oroshine_webapp.forms import (
    NewUserForm, UserProfileForm, AppointmentForm
)
from oroshine_webapp.models import UserProfile, DOCTOR_CHOICES, TIME_SLOTS


class NewUserFormTest(TestCase):
    """Test user registration form"""
    
    def test_valid_form(self):
        """Test form with valid data"""
        form = NewUserForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertTrue(form.is_valid())
        
    def test_missing_email(self):
        """Test form without email"""
        form = NewUserForm(data={
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        
    def test_invalid_email(self):
        """Test form with invalid email"""
        form = NewUserForm(data={
            'username': 'newuser',
            'email': 'not-an-email',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertFalse(form.is_valid())
        
    def test_password_mismatch(self):
        """Test form with mismatched passwords"""
        form = NewUserForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        
    def test_weak_password(self):
        """Test form with weak password"""
        form = NewUserForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': '123',
            'password2': '123',
        })
        self.assertFalse(form.is_valid())
        
    def test_duplicate_username(self):
        """Test form with existing username"""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='pass'
        )
        
        form = NewUserForm(data={
            'username': 'existing',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        
    def test_form_save(self):
        """Test form saves user correctly"""
        form = NewUserForm(data={
            'username': 'savetest',
            'email': 'save@example.com',
            'first_name': 'Save',
            'last_name': 'Test',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        
        self.assertTrue(form.is_valid())
        user = form.save()
        
        self.assertEqual(user.username, 'savetest')
        self.assertEqual(user.email, 'save@example.com')
        self.assertEqual(user.first_name, 'Save')
        self.assertEqual(user.last_name, 'Test')
        self.assertTrue(user.check_password('SecurePass123!'))


class UserProfileFormTest(TestCase):
    """Test user profile form"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        self.profile = UserProfile.objects.create(user=self.user)
        
    def test_valid_form(self):
        """Test form with valid data"""
        form = UserProfileForm(
            data={
                'first_name': 'Updated',
                'last_name': 'Name',
                'email': 'updated@example.com',
                'phone': '9876543210',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'zip_code': '400001',
            },
            instance=self.profile
        )
        self.assertTrue(form.is_valid())
        
    def test_invalid_email(self):
        """Test form with invalid email"""
        form = UserProfileForm(
            data={
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'not-valid',
            },
            instance=self.profile
        )
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        
    def test_form_initial_values(self):
        """Test form loads user data as initial values"""
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()
        
        form = UserProfileForm(instance=self.profile)
        
        self.assertEqual(form.fields['first_name'].initial, 'John')
        self.assertEqual(form.fields['last_name'].initial, 'Doe')
        self.assertEqual(form.fields['email'].initial, 'test@example.com')
        
    def test_form_save_updates_user(self):
        """Test form save updates user model"""
        form = UserProfileForm(
            data={
                'first_name': 'NewFirst',
                'last_name': 'NewLast',
                'email': 'newemail@example.com',
                'phone': '1234567890',
            },
            instance=self.profile
        )
        
        self.assertTrue(form.is_valid())
        profile = form.save()
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewFirst')
        self.assertEqual(self.user.last_name, 'NewLast')
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertEqual(profile.phone, '1234567890')


class AppointmentFormTest(TestCase):
    """Test appointment booking form"""
    
    def test_valid_form(self):
        """Test form with valid data"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        form = AppointmentForm(data={
            'name': 'Test Patient',
            'email': 'patient@example.com',
            'phone': '9876543210',
            'date': tomorrow.isoformat(),
            'time': TIME_SLOTS[0][0],
            'doctor': DOCTOR_CHOICES[0][0],
            'service': 'Consultation',
            'message': 'First visit',
        })
        
        self.assertTrue(form.is_valid())
        
    def test_missing_required_fields(self):
        """Test form with missing required fields"""
        form = AppointmentForm(data={
            'name': 'Test Patient',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('date', form.errors)
        self.assertIn('time', form.errors)
        self.assertIn('doctor_email', form.errors)
        self.assertIn('service', form.errors)
        
    def test_invalid_email(self):
        """Test form with invalid email"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        form = AppointmentForm(data={
            'name': 'Test Patient',
            'email': 'not-an-email',
            'date': tomorrow.isoformat(),
            'time': TIME_SLOTS[0][0],
            'doctor_email': DOCTOR_CHOICES[0][0],
            'service': 'Consultation',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        
    def test_invalid_date_format(self):
        """Test form with invalid date format"""
        form = AppointmentForm(data={
            'name': 'Test Patient',
            'email': 'patient@example.com',
            'date': 'not-a-date',
            'time': TIME_SLOTS[0][0],
            'doctor_email': DOCTOR_CHOICES[0][0],
            'service': 'Consultation',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)
        
    def test_invalid_time_choice(self):
        """Test form with invalid time choice"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        form = AppointmentForm(data={
            'name': 'Test Patient',
            'email': 'patient@example.com',
            'date': tomorrow.isoformat(),
            'time': '99:99:99',  # Invalid time
            'doctor_email': DOCTOR_CHOICES[0][0],
            'service': 'Consultation',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('time', form.errors)
        
    def test_invalid_doctor_choice(self):
        """Test form with invalid doctor choice"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        form = AppointmentForm(data={
            'name': 'Test Patient',
            'email': 'patient@example.com',
            'date': tomorrow.isoformat(),
            'time': TIME_SLOTS[0][0],
            'doctor_email': 'fake@example.com',
            'service': 'Consultation',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('doctor_email', form.errors)
        
    def test_optional_fields(self):
        """Test form with optional fields omitted"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        form = AppointmentForm(data={
            'name': 'Test Patient',
            'email': 'patient@example.com',
            'date': tomorrow.isoformat(),
            'time': TIME_SLOTS[0][0],
            'doctor_email': DOCTOR_CHOICES[0][0],
            'service': 'Consultation',
            # phone and message are optional
        })
        
        self.assertTrue(form.is_valid())
        
    def test_service_choices_loaded(self):
        """Test form loads service choices dynamically"""
        form = AppointmentForm()
        
        # Should have choices loaded
        self.assertTrue(len(form.fields['service'].choices) > 0)