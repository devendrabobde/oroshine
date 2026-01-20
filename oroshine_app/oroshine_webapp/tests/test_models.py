"""
Comprehensive tests for models
Run: python manage.py test oroshine_webapp.tests.test_models
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError
from datetime import timedelta

from oroshine_webapp.models import (
    Appointment, Contact, UserProfile,
    Doctor, TIME_SLOTS
)


class UserProfileModelTest(TestCase):
    """Test UserProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        
    def test_profile_creation(self):
        """Test profile can be created"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user, self.user)
        
    def test_profile_str(self):
        """Test profile string representation"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), f"{self.user.username}'s Profile")
        
    def test_profile_fields(self):
        """Test profile fields can be set"""
        profile = UserProfile.objects.create(
            user=self.user,
            phone='9876543210',
            city='Mumbai',
            state='Maharashtra',
            zip_code='400001',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='1234567890',
            medical_history='No major issues',
            allergies='None',
        )
        
        self.assertEqual(profile.phone, '9876543210')
        self.assertEqual(profile.city, 'Mumbai')
        self.assertEqual(profile.state, 'Maharashtra')
        
    def test_one_to_one_relationship(self):
        """Test one-to-one relationship with User"""
        profile = UserProfile.objects.create(user=self.user)
        
        # Can't create another profile for same user
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(user=self.user)


class AppointmentModelTest(TestCase):
    """Test Appointment model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='pass'
        )
        self.tomorrow = (timezone.now() + timedelta(days=1)).date()
        
    def test_appointment_creation(self):
        """Test appointment can be created"""
        appt = Appointment.objects.create(
            user=self.user,
            name='Test Patient',
            email='patient@example.com',
            phone='9876543210',
            date=self.tomorrow,
            time=TIME_SLOTS[0][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
            status='pending',
        )
        
        self.assertIsNotNone(appt)
        self.assertEqual(appt.user, self.user)
        self.assertEqual(appt.status, 'pending')
        
    def test_appointment_str(self):
        """Test appointment string representation"""
        appt = Appointment.objects.create(
            user=self.user,
            name='Test Patient',
            email='patient@example.com',
            date=self.tomorrow,
            time=TIME_SLOTS[0][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
        )
        
        expected = f"Appointment: Test Patient on {self.tomorrow}"
        self.assertEqual(str(appt), expected)
        
    def test_appointment_default_status(self):
        """Test default status is pending"""
        appt = Appointment.objects.create(
            user=self.user,
            name='Test Patient',
            email='patient@example.com',
            date=self.tomorrow,
            time=TIME_SLOTS[0][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
        )
        
        self.assertEqual(appt.status, 'pending')
        
    def test_appointment_timestamps(self):
        """Test auto timestamps"""
        appt = Appointment.objects.create(
            user=self.user,
            name='Test Patient',
            email='patient@example.com',
            date=self.tomorrow,
            time=TIME_SLOTS[0][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
        )
        
        self.assertIsNotNone(appt.created_at)
        self.assertIsNotNone(appt.updated_at)
        
    def test_appointment_ordering(self):
        """Test appointments are ordered by date descending"""
        appt1 = Appointment.objects.create(
            user=self.user,
            name='Patient 1',
            email='p1@example.com',
            date=self.tomorrow,
            time=TIME_SLOTS[0][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
        )
        
        day_after = self.tomorrow + timedelta(days=1)
        appt2 = Appointment.objects.create(
            user=self.user,
            name='Patient 2',
            email='p2@example.com',
            date=day_after,
            time=TIME_SLOTS[0][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
        )
        
        appointments = list(Appointment.objects.all())
        # Should be ordered by -date (newest first)
        self.assertEqual(appointments[0], appt2)
        self.assertEqual(appointments[1], appt1)
        
    def test_unique_constraint_active_slots(self):
        """Test unique constraint for active appointment slots"""
        # Create first appointment
        Appointment.objects.create(
            user=self.user,
            name='Patient 1',
            email='p1@example.com',
            date=self.tomorrow,
            time=TIME_SLOTS[0][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
            status='confirmed',
        )
        
        # Try to create duplicate - should raise error if constraint exists
        with self.assertRaises(IntegrityError):
            Appointment.objects.create(
                user=self.user,
                name='Patient 2',
                email='p2@example.com',
                date=self.tomorrow,
                time=TIME_SLOTS[0][0],
                doctor_email=DOCTOR_CHOICES[0][0],
                service='Consultation',
                status='confirmed',
            )
            
    def test_cancelled_slots_allow_rebooking(self):
        """Test cancelled appointments don't block slots"""
        # Create cancelled appointment
        Appointment.objects.create(
            user=self.user,
            name='Patient 1',
            email='p1@example.com',
            date=self.tomorrow,
            time=TIME_SLOTS[0][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
            status='cancelled',
        )
        
        # Should allow new appointment in same slot
        appt2 = Appointment.objects.create(
            user=self.user,
            name='Patient 2',
            email='p2@example.com',
            date=self.tomorrow,
            time=TIME_SLOTS[0][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
            status='confirmed',
        )
        
        self.assertIsNotNone(appt2)


class ContactModelTest(TestCase):
    """Test Contact model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )
        
    def test_contact_creation(self):
        """Test contact can be created"""
        contact = Contact.objects.create(
            user=self.user,
            name='Test User',
            email='test@example.com',
            subject='Inquiry',
            message='Test message',
        )
        
        self.assertIsNotNone(contact)
        self.assertEqual(contact.user, self.user)
        
    def test_contact_str(self):
        """Test contact string representation"""
        contact = Contact.objects.create(
            user=self.user,
            name='Test User',
            email='test@example.com',
            subject='Inquiry',
            message='Test message',
        )
        
        self.assertIn('Test User', str(contact))
        
    def test_contact_timestamps(self):
        """Test contact has timestamps"""
        contact = Contact.objects.create(
            user=self.user,
            name='Test User',
            email='test@example.com',
            subject='Inquiry',
            message='Test message',
        )
        
        self.assertIsNotNone(contact.created_at)
        
    def test_contact_ordering(self):
        """Test contacts ordered by creation date descending"""
        contact1 = Contact.objects.create(
            user=self.user,
            name='User 1',
            email='u1@example.com',
            subject='Subject 1',
            message='Message 1',
        )
        
        contact2 = Contact.objects.create(
            user=self.user,
            name='User 2',
            email='u2@example.com',
            subject='Subject 2',
            message='Message 2',
        )
        
        contacts = list(Contact.objects.all())
        self.assertEqual(contacts[0], contact2)
        self.assertEqual(contacts[1], contact1)
        
    def test_contact_user_can_be_null(self):
        """Test contact can be created without user (for non-authenticated)"""
        contact = Contact.objects.create(
            user=None,
            name='Anonymous',
            email='anon@example.com',
            subject='Question',
            message='Anonymous message',
        )
        
        self.assertIsNotNone(contact)
        self.assertIsNone(contact.user)


class AppointmentManagerTest(TestCase):
    """Test custom appointment manager methods"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            password='pass'
        )
        self.tomorrow = (timezone.now() + timedelta(days=1)).date()
        
    def test_with_counts_by_status(self):
        """Test appointment count aggregation by status"""
        # Create various appointments
        Appointment.objects.create(
            user=self.user,
            name='P1', email='p1@test.com',
            date=self.tomorrow,
            time=TIME_SLOTS[0][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
            status='pending',
        )
        
        Appointment.objects.create(
            user=self.user,
            name='P2', email='p2@test.com',
            date=self.tomorrow,
            time=TIME_SLOTS[1][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
            status='confirmed',
        )
        
        Appointment.objects.create(
            user=self.user,
            name='P3', email='p3@test.com',
            date=self.tomorrow,
            time=TIME_SLOTS[2][0],
            doctor_email=DOCTOR_CHOICES[0][0],
            service='Consultation',
            status='completed',
        )
        
        stats = Appointment.objects.with_counts_by_status(self.user.id)
        
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['pending'], 1)
        self.assertEqual(stats['completed'], 1)