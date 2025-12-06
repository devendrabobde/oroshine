import logging
import requests
from datetime import datetime, timedelta
from django.conf import settings
from celery import shared_task
from django.core.cache import cache

from .models import Appointment, Contact
from .emails import send_appointment_emails, send_contact_emails

logger = logging.getLogger(__name__)


# -------------------------------------------------------
# ASYNC: SEND CONTACT EMAILS (Admin + User)
# -------------------------------------------------------
@shared_task(bind=True, max_retries=3, default_retry_delay=30, autoretry_for=(Exception,))
def send_contact_email_task(self, contact_id, user_ip):
    """
    Send contact form emails asynchronously
    Retries 3 times with 30s delay on failure
    """
    try:
        contact = Contact.objects.select_related('user').get(id=contact_id)
        send_contact_emails(contact, user_ip)
        
        # Mark as processed in cache
        cache.set(f'contact_email_sent_{contact_id}', True, timeout=3600)
        
        logger.info(f"Contact emails sent successfully for ID: {contact_id}")
        return {'status': 'success', 'contact_id': contact_id}

    except Contact.DoesNotExist:
        logger.error(f"Contact with ID {contact_id} does not exist")
        return {'status': 'error', 'message': 'Contact not found'}
    
    except Exception as e:
        logger.error(f"Error sending contact emails for ID {contact_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)


# -------------------------------------------------------
# ASYNC: SEND APPOINTMENT EMAILS (Admin + User)
# -------------------------------------------------------
@shared_task(bind=True, max_retries=3, default_retry_delay=30, autoretry_for=(Exception,))
def send_appointment_email_task(self, appointment_id):
    """
    Send appointment confirmation emails asynchronously
    """
    try:
        appointment = Appointment.objects.select_related('user').get(id=appointment_id)
        send_appointment_emails(appointment)
        
        # Mark as sent in cache
        cache.set(f'appointment_email_sent_{appointment_id}', True, timeout=3600)
        
        logger.info(f"Appointment emails sent successfully for ID: {appointment_id}")
        return {'status': 'success', 'appointment_id': appointment_id}

    except Appointment.DoesNotExist:
        logger.error(f"Appointment with ID {appointment_id} does not exist")
        return {'status': 'error', 'message': 'Appointment not found'}
    
    except Exception as e:
        logger.error(f"Error sending appointment emails for ID {appointment_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)


# -------------------------------------------------------
# ASYNC: CREATE GOOGLE CALENDAR EVENT USING NOCODEAPI
# -------------------------------------------------------
@shared_task(bind=True, max_retries=2, default_retry_delay=20)
def create_calendar_event_task(self, appointment_id):
    """
    Create Google Calendar event asynchronously
    """
    try:
        appointment = Appointment.objects.select_related('user').get(id=appointment_id)

        start_dt = datetime.combine(appointment.date, appointment.time)
        end_dt = start_dt + timedelta(minutes=30)

        url = f"{settings.NOCODEAPI_BASE_URL}/event"

        payload = {
            "summary": f"🦷 Dental Appointment: {appointment.get_service_display()}",
            "description": f"""
Service: {appointment.get_service_display()}
Patient: {appointment.name}
Email: {appointment.email}
Phone: {appointment.phone}
Doctor: {appointment.doctor_email}
Message: {appointment.message or 'N/A'}
Status: {appointment.get_status_display()}
            """.strip(),
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "attendees": [
                {"email": appointment.email},
                {"email": appointment.doctor_email},
            ],
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        # Store event ID in appointment
        if 'id' in result:
            appointment.calendar_event_id = result['id']
            appointment.save(update_fields=['calendar_event_id'])
        
        logger.info(f"Calendar event created successfully for appointment ID: {appointment_id}")
        return {'status': 'success', 'event_id': result.get('id'), 'appointment_id': appointment_id}

    except Appointment.DoesNotExist:
        logger.error(f"Appointment with ID {appointment_id} does not exist")
        return {'status': 'error', 'message': 'Appointment not found'}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Calendar event creation failed for appointment {appointment_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    
    except Exception as e:
        logger.error(f"Unexpected error creating calendar event for {appointment_id}: {e}")
        raise self.retry(exc=e, countdown=60)


# -------------------------------------------------------
# ASYNC: SEND APPOINTMENT REMINDER (24 HOURS BEFORE)
# -------------------------------------------------------
@shared_task
def send_appointment_reminder_task(appointment_id):
    """
    Send reminder email 24 hours before appointment
    """
    try:
        appointment = Appointment.objects.select_related('user').get(id=appointment_id)
        
        if appointment.status != 'confirmed':
            logger.info(f"Skipping reminder for appointment {appointment_id} - status: {appointment.status}")
            return {'status': 'skipped', 'reason': 'not_confirmed'}
        
        # Send reminder email
        from .emails import send_appointment_reminder_email
        send_appointment_reminder_email(appointment)
        
        logger.info(f"Reminder sent for appointment ID: {appointment_id}")
        return {'status': 'success', 'appointment_id': appointment_id}
    
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found for reminder")
        return {'status': 'error', 'message': 'Appointment not found'}
    
    except Exception as e:
        logger.error(f"Error sending reminder for appointment {appointment_id}: {e}")
        raise


# -------------------------------------------------------
# PERIODIC TASK: CHECK AND SEND REMINDERS
# -------------------------------------------------------
@shared_task
def check_and_send_reminders():
    """
    Periodic task to check appointments and send reminders
    Run this daily
    """
    tomorrow = datetime.now().date() + timedelta(days=1)
    
    appointments = Appointment.objects.filter(
        date=tomorrow,
        status='confirmed'
    ).select_related('user')
    
    count = 0
    for appointment in appointments:
        # Check if reminder already sent
        cache_key = f'reminder_sent_{appointment.id}'
        if not cache.get(cache_key):
            send_appointment_reminder_task.delay(appointment.id)
            cache.set(cache_key, True, timeout=86400)  # 24 hours
            count += 1
    
    logger.info(f"Queued {count} appointment reminders")
    return {'status': 'success', 'reminders_queued': count}


# -------------------------------------------------------
# ASYNC: UPDATE APPOINTMENT STATUS
# -------------------------------------------------------
@shared_task
def update_appointment_status_task(appointment_id, new_status):
    """
    Update appointment status asynchronously
    """
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        old_status = appointment.status
        appointment.status = new_status
        appointment.save(update_fields=['status', 'updated_at'])
        
        logger.info(f"Appointment {appointment_id} status updated: {old_status} -> {new_status}")
        return {'status': 'success', 'appointment_id': appointment_id, 'new_status': new_status}
    
    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_id} not found")
        return {'status': 'error', 'message': 'Appointment not found'}
    
    except Exception as e:
        logger.error(f"Error updating appointment {appointment_id}: {e}")
        raise