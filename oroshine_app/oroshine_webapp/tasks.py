import logging
import requests
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone
from django.core.cache import cache
import logging

from .models import Appointment
from .emails import send_appointment_emails
logger = logging.getLogger(__name__)



@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={'max_retries': 3},
)
def send_appointment_email_task(self, appointment_id):
    """
    Celery wrapper for sending appointment emails
    """

    close_old_connections()

    cache_key = f"appointment_email_sent:{appointment_id}"

    # 🛑 Idempotency (no duplicate emails)
    if cache.get(cache_key):
        logger.info(
            f"[Email] Already sent for appointment {appointment_id}"
        )
        return "skipped"

    appointment = Appointment.objects.get(id=appointment_id)

    send_appointment_emails(appointment)

    cache.set(cache_key, True, 60 * 60 * 24)  # 24h
    logger.info(
        f"[Email] Successfully sent for appointment {appointment_id}"
    )

    return "sent"







@shared_task(
    bind=True,
    autoretry_for=(requests.Timeout, requests.ConnectionError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3
)
def create_calendar_event_task(self, appointment_id):
    """
    Create Google Calendar event via NoCodeAPI.
    Optimized and efficient:
    - Uses select_related for doctor
    - Idempotent (skips if event already exists)
    - Handles known errors gracefully
    """
    close_old_connections()

    try:
        # Fetch appointment with related doctor efficiently
        appt = (
            Appointment.objects
            .select_related('doctor')
            .only(
                'id', 'date', 'time', 'name', 'email',
                'service', 'message', 'status', 'calendar_event_id',
                'doctor__id', 'doctor__email'
            )
            .get(id=appointment_id)
        )

        # -----------------------------
        # Idempotency check
        # -----------------------------
        if appt.calendar_event_id:
            logger.info(f"[Calendar] Event already exists for appointment {appointment_id}")
            return {
                'status': 'skipped',
                'reason': 'already_created',
                'event_id': appt.calendar_event_id
            }

        # -----------------------------
        # Validate appointment and doctor
        # -----------------------------
        if appt.status not in ['confirmed', 'pending']:            
            logger.info(f"[Calendar] Appointment {appointment_id} status={appt.status}, skipping")
            return {
                'status': 'skipped',
                'reason': f'invalid_status_{appt.status}'
            }

        if not appt.doctor or not appt.doctor.email:
            logger.error(f"[Calendar] Appointment {appointment_id} has invalid doctor info")
            return {'status': 'invalid_doctor'}
        # Prepare timezone-aware datetimes
        # -----------------------------
        # 1. Ensure date is a proper object
        if isinstance(appt.date, str):
            appt_date = datetime.strptime(appt.date, "%Y-%m-%d").date()
        else:
            appt_date = appt.date

        # 2. Ensure time is a proper object
        if isinstance(appt.time, str):
            # Handle potential seconds in time string (HH:MM:SS)
            time_str = appt.time
            if len(time_str.split(':')) == 2:
                 time_str += ":00" # Add seconds if missing
            appt_time = datetime.strptime(time_str, "%H:%M:%S").time()
        else:
            appt_time = appt.time

        # 3. Combine safely
        start_dt = timezone.make_aware(datetime.combine(appt_date, appt_time), timezone.get_current_timezone())
        end_dt = start_dt + timedelta(minutes=30)

        # -----------------------------
        # Prepare API payload
        # -----------------------------
        payload = {
            "summary": f"Dental Appointment: {appt.service}",
            "description": (
                f"Patient: {appt.name}\n"
                f"Patient Email: {appt.email}\n"
                f"Doctor Email: {appt.doctor.email}\n"
                f"Message: {appt.message or 'N/A'}"
            ),
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "attendees": [
                {"email": appt.email},
                {"email": appt.doctor.email}
            ]
        }

        # -----------------------------
        # Make request to NoCodeAPI
        # -----------------------------
        url = f"{settings.NOCODEAPI_BASE_URL}/event"
        headers = {
            "Authorization": f"Bearer {settings.NOCODEAPI_KEY}",
            "Content-Type": "application/json"
        }
        if settings.NOCODEAPI_KEY:
            headers["Authorization"] = f"Bearer {settings.NOCODEAPI_KEY}"
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        # Auth errors → do NOT retry
        if response.status_code in (401, 403):
            logger.critical("[Calendar] Unauthorized request to NoCodeAPI. Check NOCODEAPI_KEY.")
            return {'status': 'auth_error', 'code': response.status_code, 'response': response.text}

        response.raise_for_status()
        data = response.json()
        event_id = data.get("id")

        if not event_id:
            logger.error(f"[Calendar] No event ID returned for appointment {appointment_id}")
            return {'status': 'api_error', 'reason': 'missing_event_id', 'response': data}

        # -----------------------------
        # Persist event ID efficiently
        # -----------------------------
        Appointment.objects.filter(id=appointment_id).update(calendar_event_id=event_id)

        logger.info(f"[Calendar] Event created successfully appointment={appointment_id} event={event_id}")

        return {'status': 'success', 'appointment_id': appointment_id, 'event_id': event_id}

    # -----------------------------
    # Known failures
    # -----------------------------
    except Appointment.DoesNotExist:
        logger.warning(f"[Calendar] Appointment {appointment_id} not found")
        return {'status': 'not_found'}

    except requests.Timeout as exc:
        logger.error(f"[Calendar] Timeout for appointment {appointment_id}")
        raise self.retry(exc=exc)

    except requests.HTTPError as exc:
        status_code = exc.response.status_code
        logger.error(f"[Calendar] HTTP {status_code} error appointment {appointment_id}")
        if status_code >= 500:
            raise self.retry(exc=exc)
        return {'status': 'api_error', 'code': status_code, 'response': exc.response.text}

    except Exception as exc:
        logger.exception(f"[Calendar] Unexpected error appointment {appointment_id}")
        return {'status': 'error', 'message': str(exc)}

    finally:
        close_old_connections()
