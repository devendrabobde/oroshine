"""
Tests for Celery tasks
Run: python manage.py test oroshine_webapp.tests.test_tasks
"""

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from unittest.mock import patch, MagicMock
import requests

from oroshine_webapp.models import Appointment, Contact
from oroshine_webapp.tasks import (
    send_appointment_email_task,
    send_contact_email_task,
    create_calendar_event_task,
    send_appointment_reminder_task,
    check_and_send_reminders,
)


# Use synchronous celery for testing
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AppointmentEmailTaskTest(TestCase):
    """Test appointment email task"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='pass'
        )
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        self.appointment = Appointment.objects.create(
            user=self.user,
            name='Test Patient',
            email='patient@example.com',
            phone='9876543210',
            date=tomorrow,
            time='10:00:00',
            doctor_email='doctor@clinic.com',
            service='Consultation',
            status='pending',
        )
        cache.clear()
        
    def tearDown(self):
        cache.clear()
        
    def test_send_appointment_email_success(self):
        """Test successful email sending"""
        result = send_appointment_email_task(self.appointment.id)
        
        self.assertEqual(result['status'], 'success')
        
        # Check emails were sent (2: admin + user)
        self.assertEqual(len(mail.outbox), 2)
        
        # Check cache was set
        cache_key = f'appointment_email_sent:{self.appointment.id}'
        self.assertTrue(cache.get(cache_key))
        
    def test_send_appointment_email_duplicate_prevention(self):
        """Test email is not sent twice"""
        # Send first time
        send_appointment_email_task(self.appointment.id)
        self.assertEqual(len(mail.outbox), 2)
        
        # Try to send again
        result = send_appointment_email_task(self.appointment.id)
        
        # Should skip
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'already_sent')
        
        # Still only 2 emails
        self.assertEqual(len(mail.outbox), 2)
        
    def test_send_appointment_email_invalid_status(self):
        """Test email not sent for cancelled appointments"""
        self.appointment.status = 'cancelled'
        self.appointment.save()
        
        result = send_appointment_email_task(self.appointment.id)
        
        self.assertEqual(result['status'], 'skipped')
        self.assertIn('invalid_status', result['reason'])
        
    def test_send_appointment_email_not_found(self):
        """Test handling non-existent appointment"""
        result = send_appointment_email_task(99999)
        self.assertEqual(result['status'], 'not_found')


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ContactEmailTaskTest(TestCase):
    """Test contact form email task"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='pass'
        )
        
        self.contact = Contact.objects.create(
            user=self.user,
            name='Test User',
            email='test@example.com',
            subject='Inquiry',
            message='Test message',
        )
        cache.clear()
        
    def tearDown(self):
        cache.clear()
        
    def test_send_contact_email_success(self):
        """Test successful contact email"""
        result = send_contact_email_task(
            self.contact.id,
            user_ip='127.0.0.1'
        )
        
        self.assertEqual(result['status'], 'success')
        
        # Check emails sent (2: admin + user)
        self.assertEqual(len(mail.outbox), 2)
        
    def test_send_contact_email_duplicate_prevention(self):
        """Test contact email only sent once"""
        send_contact_email_task(self.contact.id, '127.0.0.1')
        self.assertEqual(len(mail.outbox), 2)
        
        # Try again
        result = send_contact_email_task(self.contact.id, '127.0.0.1')
        
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(len(mail.outbox), 2)
        
    def test_send_contact_email_not_found(self):
        """Test handling non-existent contact"""
        result = send_contact_email_task(99999, '127.0.0.1')
        self.assertEqual(result['status'], 'not_found')


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class CalendarEventTaskTest(TestCase):
    """Test calendar event creation task"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            password='pass'
        )
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        self.appointment = Appointment.objects.create(
            user=self.user,
            name='Test Patient',
            email='patient@example.com',
            date=tomorrow,
            time='10:00:00',
            doctor_email='doctor@clinic.com',
            service='Consultation',
            status='pending',
        )
        
    @patch('oroshine_webapp.tasks.requests.post')
    def test_create_calendar_event_success(self, mock_post):
        """Test successful calendar event creation"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'event_123'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = create_calendar_event_task(self.appointment.id)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['event_id'], 'event_123')
        
        # Verify appointment was updated
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.calendar_event_id, 'event_123')
        
    @patch('oroshine_webapp.tasks.requests.post')
    def test_create_calendar_event_timeout(self, mock_post):
        """Test handling timeout"""
        mock_post.side_effect = requests.Timeout('Connection timeout')
        
        # Should retry or return error
        result = create_calendar_event_task(self.appointment.id)
        
        # Result depends on retry logic
        self.assertIn('status', result)
        
    @patch('oroshine_webapp.tasks.requests.post')
    def test_create_calendar_event_http_error(self, mock_post):
        """Test handling HTTP errors"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        http_error = requests.HTTPError('Bad request')
        http_error.response = mock_response
        mock_post.side_effect = http_error
        
        result = create_calendar_event_task(self.appointment.id)
        
        self.assertEqual(result['status'], 'api_error')
        
    def test_create_calendar_event_not_found(self):
        """Test handling non-existent appointment"""
        result = create_calendar_event_task(99999)
        self.assertEqual(result['status'], 'not_found')


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ReminderTaskTest(TestCase):
    """Test appointment reminder tasks"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient',
            email='patient@example.com',
            password='pass'
        )
        cache.clear()
        
    def tearDown(self):
        cache.clear()
        
    def test_send_reminder_confirmed_appointment(self):
        """Test reminder sent for confirmed appointment"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        appointment = Appointment.objects.create(
            user=self.user,
            name='Test Patient',
            email='patient@example.com',
            date=tomorrow,
            time='10:00:00',
            doctor_email='doctor@clinic.com',
            service='Consultation',
            status='confirmed',
        )
        
        result = send_appointment_reminder_task(appointment.id)
        
        self.assertEqual(result['status'], 'sent')
        self.assertEqual(len(mail.outbox), 1)
        
    def test_send_reminder_pending_appointment(self):
        """Test reminder skipped for pending appointment"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        appointment = Appointment.objects.create(
            user=self.user,
            name='Test Patient',
            email='patient@example.com',
            date=tomorrow,
            time='10:00:00',
            doctor_email='doctor@clinic.com',
            service='Consultation',
            status='pending',
        )
        
        result = send_appointment_reminder_task(appointment.id)
        
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(len(mail.outbox), 0)
        
    def test_check_and_send_reminders_queues_tasks(self):
        """Test reminder check queues tasks for tomorrow's appointments"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        # Create confirmed appointments for tomorrow
        for i in range(3):
            Appointment.objects.create(
                user=self.user,
                name=f'Patient {i}',
                email=f'patient{i}@example.com',
                date=tomorrow,
                time='10:00:00',
                doctor_email='doctor@clinic.com',
                service='Consultation',
                status='confirmed',
            )
            
        result = check_and_send_reminders()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['queued'], 3)
        
    def test_check_and_send_reminders_skips_duplicates(self):
        """Test reminder check doesn't queue duplicates"""
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        appointment = Appointment.objects.create(
            user=self.user,
            name='Patient',
            email='patient@example.com',
            date=tomorrow,
            time='10:00:00',
            doctor_email='doctor@clinic.com',
            service='Consultation',
            status='confirmed',
        )
        
        # Run once
        result1 = check_and_send_reminders()
        self.assertEqual(result1['queued'], 1)
        
        # Run again immediately
        result2 = check_and_send_reminders()
        self.assertEqual(result2['skipped'], 1)
        self.assertEqual(result2['queued'], 0)