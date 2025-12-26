import logging
import requests
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import close_old_connections
from django.core.mail import EmailMessage
from smtplib import SMTPException
import time

from .emails import (
    send_appointment_emails,
    send_contact_emails,
    send_appointment_reminder_email
)

logger = logging.getLogger(__name__)

from .metrics import celery_task_total, celery_task_duration


# Decorator to track metrics
def track_task_metrics(func):
    def wrapper(*args, **kwargs):
        task_name = func.__name__
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            celery_task_total.labels(task_name=task_name, status='success').inc()
            return result
        except Exception:
            celery_task_total.labels(task_name=task_name, status='failure').inc()
            raise
        finally:
            duration = time.time() - start_time
            celery_task_duration.labels(task_name=task_name).observe(duration)
    return wrapper

# -------------------------------------------------------
# CONTACT EMAIL TASK (IDEMPOTENT)
# -------------------------------------------------------
@shared_task(
    bind=True,
    autoretry_for=(SMTPException, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3
)
def send_contact_email_task(self, contact_id, user_ip):
    """Send contact form email with idempotency check"""
    cache_key = f'contact_email_sent:{contact_id}'
    
    # Check if already sent
    if cache.get(cache_key):
        logger.info(f"Contact email {contact_id} already sent, skipping")
        return {'status': 'skipped', 'reason': 'already_sent'}

    close_old_connections()

    from .models import Contact

    try:
        contact = (
            Contact.objects
            .select_related('user')
            .only('id', 'email', 'message', 'created_at', 'user__email')
            .get(id=contact_id)
        )

        # Send emails
        send_contact_emails(contact, user_ip)
        
        # Mark as sent (cache for 24 hours)
        cache.set(cache_key, True, 86400)
        
        logger.info(f"Contact email sent successfully for ID {contact_id}")
        return {'status': 'success', 'id': contact_id}

    except Contact.DoesNotExist:
        logger.warning(f"Contact {contact_id} not found")
        return {'status': 'not_found'}
    
    except SMTPException as exc:
        logger.error(f"SMTP error sending contact email {contact_id}: {exc}")
        raise self.retry(exc=exc)
    
    except Exception as exc:
        logger.exception(f"Unexpected error sending contact email {contact_id}")
        return {'status': 'error', 'message': str(exc)}
    
    finally:
        close_old_connections()


# -------------------------------------------------------
# APPOINTMENT EMAIL TASK (IDEMPOTENT + BETTER ERROR HANDLING)
# -------------------------------------------------------
@shared_task(
    bind=True,
    autoretry_for=(SMTPException, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
    acks_late=True
)
@track_task_metrics
def send_appointment_email_task(self, appointment_id):

    """Send appointment confirmation email with robust error handling"""
    cache_key = f'appointment_email_sent:{appointment_id}'
    
    # Check if already sent
    if cache.get(cache_key):
        logger.info(f"Appointment email {appointment_id} already sent, skipping")
        return {'status': 'skipped', 'reason': 'already_sent'}

    close_old_connections()

    from .models import Appointment

    try:
        appt = Appointment.objects.select_for_update().get(id=appointment_id)

        # appt = (
        #     Appointment.objects
        #     .only(
        #         'id', 'name', 'email', 'date', 'time',
        #         'doctor_email', 'service', 'status'
        #     )
        #     .get(id=appointment_id)
        # )
        
        # Verify appointment is still valid
        # if appt.status not in ['pending', 'confirmed']:
        #     logger.info(f"Appointment {appointment_id} status is {appt.status}, skipping email")
        #     return {'status': 'skipped', 'reason': f'invalid_status_{appt.status}'}



        if appt.email_sent_at:
            logger.info(f"Email already sent at {appt.email_sent_at}")
            return {'status': 'skipped', 'reason': 'already_sent'}
        
        if appt.status not in ['pending', 'confirmed']:
            return {'status': 'skipped', 'reason': f'invalid_status_{appt.status}'}

        # Send emails
        send_appointment_emails(appt)
        appt.email_sent_at = timezone.now()
        appt.save(update_fields=['email_sent_at'])
        
        return {'status': 'success', 'id': appointment_id}
        
        # Mark as sent (cache for 1 hour - appointment emails can be resent if needed)
        cache.set(cache_key, True, 60)
        
        logger.info(f"Appointment email sent successfully for ID {appointment_id}")
        return {'status': 'success', 'id': appointment_id}

    except Appointment.DoesNotExist:
        logger.warning(f"Appointment {appointment_id} not found")
        return {'status': 'not_found'}
    
    except SMTPException as exc:
        logger.error(f"SMTP error sending appointment email {appointment_id}: {exc}")
        # Don't retry on authentication errors - they won't resolve themselves
        if '535' in str(exc) or 'authentication' in str(exc).lower():
            logger.critical(f"SMTP Authentication failed for appointment {appointment_id}. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
            return {'status': 'auth_error', 'message': 'SMTP authentication failed'}
        raise self.retry(exc=exc)
    
    except Exception as exc:
        logger.exception(f"Unexpected error sending appointment email {appointment_id}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {'status': 'error', 'message': str(exc)}
    
    finally:
        close_old_connections()








# -------------------------------------------------------
# GOOGLE CALENDAR EVENT (NON-BLOCKING + BETTER RETRY)
# -------------------------------------------------------
@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException, requests.Timeout),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3
)
@track_task_metrics
def create_calendar_event_task(self, appointment_id):
    """Create Google Calendar event via NoCodeAPI"""
    close_old_connections()

    from .models import Appointment

    try:
        appt_data = (
            Appointment.objects
            .filter(id=appointment_id)
            .values(
                'date', 'time', 'name', 'email',
                'doctor_email', 'service', 'message', 'status'
            )
            .first()
        )

        if not appt_data:
            logger.warning(f"Appointment {appointment_id} not found for calendar event")
            return {'status': 'not_found'}

        # Build datetime
        start_dt = datetime.combine(appt_data['date'], appt_data['time'])
        end_dt = start_dt + timedelta(minutes=30)

        payload = {
            "summary": f"Dental Appointment: {appt_data['service']}",
            "description": (
                f"Patient: {appt_data['name']}\n"
                f"Email: {appt_data['email']}\n"
                f"Doctor: {appt_data['doctor_email']}\n"
                f"Message: {appt_data['message'] or 'N/A'}\n"
                f"Status: {appt_data['status']}"
            ),
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Asia/Kolkata"
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Asia/Kolkata"
            },
            "attendees": [
                {"email": appt_data['email']},
                {"email": appt_data['doctor_email']}
            ],
        }

        # Make API call with timeout
        response = requests.post(
            f"{settings.NOCODEAPI_BASE_URL}/event",
            json=payload,
            timeout=10
        )
        response.raise_for_status()

        event_data = response.json()
        event_id = event_data.get('id')
        
        if event_id:
            Appointment.objects.filter(id=appointment_id).update(
                calendar_event_id=event_id
            )
            logger.info(f"Calendar event created for appointment {appointment_id}: {event_id}")
            return {'status': 'success', 'event_id': event_id}
        else:
            logger.warning(f"No event ID returned for appointment {appointment_id}")
            return {'status': 'no_event_id', 'response': event_data}

    except requests.Timeout as exc:
        logger.error(f"Timeout creating calendar event for {appointment_id}")
        raise self.retry(exc=exc)
    
    except requests.HTTPError as exc:
        logger.error(f"HTTP error creating calendar event for {appointment_id}: {exc}")
        if exc.response.status_code >= 500:
            raise self.retry(exc=exc)
        return {'status': 'api_error', 'code': exc.response.status_code}
    
    except Exception as exc:
        logger.exception(f"Unexpected error creating calendar event for {appointment_id}")
        return {'status': 'error', 'message': str(exc)}
    
    finally:
        close_old_connections()


# -------------------------------------------------------
# REMINDER EMAIL (SINGLE APPOINTMENT)
# -------------------------------------------------------
@shared_task(
    bind=True,
    autoretry_for=(SMTPException,),
    retry_backoff=True,
    max_retries=2
)
@track_task_metrics
def send_appointment_reminder_task(self, appointment_id):
    """Send appointment reminder 24h before"""
    close_old_connections()

    from .models import Appointment

    try:
        appt = Appointment.objects.select_for_update().get(
                id=appointment_id,
                status='confirmed',
                reminder_sent_at__isnull=True  # Add this field to model
            )


        send_appointment_reminder_email(appt)
        appt.reminder_sent_at = timezone.now()
        appt.save(update_fields=['reminder_sent_at'])

        # Only send for confirmed appointments
        if appt.status != 'confirmed':
            logger.info(f"Appointment {appointment_id} not confirmed, skipping reminder")
            return {'status': 'skipped', 'reason': 'not_confirmed'}

        send_appointment_reminder_email(appt)
        logger.info(f"Reminder sent for appointment {appointment_id}")
        return {'status': 'sent', 'id': appointment_id}

    except Appointment.DoesNotExist:
        logger.warning(f"Appointment {appointment_id} not found for reminder")
        return {'status': 'not_found'}
    
    except SMTPException as exc:
        logger.error(f"SMTP error sending reminder for {appointment_id}: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {'status': 'error', 'message': str(exc)}
    
    finally:
        close_old_connections()


# -------------------------------------------------------
# DAILY REMINDER SCAN (OPTIMIZED)
# -------------------------------------------------------
@shared_task(bind=True)
def check_and_send_reminders(self):
    """Scan and queue reminder emails for tomorrow's appointments"""
    close_old_connections()

    from .models import Appointment

    tomorrow = (datetime.now() + timedelta(days=1)).date()

    try:
        # Get IDs of confirmed appointments for tomorrow
        appointment_ids = list(
            Appointment.objects
            .filter(date=tomorrow, status='confirmed')
            .values_list('id', flat=True)
        )

        queued = 0
        skipped = 0

        for appt_id in appointment_ids:
            cache_key = f'reminder_sent:{appt_id}'
            
            # Check if already sent
            if cache.get(cache_key):
                skipped += 1
                continue
            
            # Queue the task
            send_appointment_reminder_task.apply_async(
                args=[appt_id],
                countdown=0
            )
            
            # Mark as queued (cache for 25 hours to prevent duplicate sends)
            cache.set(cache_key, True, 90000)
            queued += 1

        logger.info(f"Reminder check complete: {queued} queued, {skipped} skipped")
        return {
            'status': 'success',
            'date': str(tomorrow),
            'queued': queued,
            'skipped': skipped
        }

    except Exception as exc:
        logger.exception("Error in reminder check task")
        return {'status': 'error', 'message': str(exc)}
    
    finally:
        close_old_connections()


# -------------------------------------------------------
# STATUS UPDATE (FAST, NO ORM LOAD)
# -------------------------------------------------------
@shared_task(bind=True)
def update_appointment_status_task(self, appointment_id, new_status):
    """Update appointment status - lightweight task"""
    close_old_connections()

    from .models import Appointment

    try:
        updated = Appointment.objects.filter(id=appointment_id).update(
            status=new_status,
            updated_at=datetime.now()
        )

        if updated:
            # Invalidate related caches if needed
            logger.info(f"Appointment {appointment_id} status updated to {new_status}")
            return {'status': 'success', 'id': appointment_id, 'new_status': new_status}
        else:
            logger.warning(f"Appointment {appointment_id} not found for status update")
            return {'status': 'not_found'}

    except Exception as exc:
        logger.exception(f"Error updating appointment {appointment_id} status")
        return {'status': 'error', 'message': str(exc)}
    
    finally:
        close_old_connections()


# -------------------------------------------------------
# SOCIAL AVATAR DOWNLOAD (CPU SAFE)
# -------------------------------------------------------
@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException, IOError),
    retry_backoff=True,
    max_retries=2
)
def download_social_avatar_task(self, user_id, avatar_url):
    """Download and optimize user avatar from social login"""
    close_old_connections()

    from django.contrib.auth.models import User
    from django.core.files.base import ContentFile
    from io import BytesIO
    from PIL import Image
    from .models import UserProfile

    try:
        profile = (
            UserProfile.objects
            .select_related('user')
            .only('id', 'avatar')
            .get(user_id=user_id)
        )

        # Download image with timeout
        response = requests.get(avatar_url, timeout=10, stream=True)
        response.raise_for_status()

        # Process image
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGB if needed
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        elif img.mode == 'RGBA':
            # Handle transparency
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background

        # Resize to thumbnail
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)

        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        buffer.seek(0)

        # Save to profile
        profile.avatar.save(
            f"avatar_{user_id}.jpg",
            ContentFile(buffer.read()),
            save=True
        )

        logger.info(f"Avatar downloaded for user {user_id}")
        return {'status': 'success', 'user_id': user_id}

    except (User.DoesNotExist, UserProfile.DoesNotExist):
        logger.warning(f"User/Profile {user_id} not found for avatar download")
        return {'status': 'not_found'}
    
    except requests.RequestException as exc:
        logger.error(f"Error downloading avatar for user {user_id}: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {'status': 'download_error', 'message': str(exc)}
    
    except Exception as exc:
        logger.exception(f"Unexpected error processing avatar for user {user_id}")
        return {'status': 'error', 'message': str(exc)}
    
    finally:
        close_old_connections()


# -------------------------------------------------------
# CACHE CLEANUP TASK (MAINTENANCE)
# -------------------------------------------------------
@shared_task(bind=True)
def cleanup_old_cache(self):
    """Clean up old cache entries - runs daily"""
    try:
        from django.core.cache import cache
        
        # This is a placeholder - implement based on your cache patterns
        # For Redis, you might want to use SCAN to find old keys
        
        logger.info("Cache cleanup task executed")
        return {'status': 'success'}
    
    except Exception as exc:
        logger.exception("Error in cache cleanup task")
        return {'status': 'error', 'message': str(exc)}