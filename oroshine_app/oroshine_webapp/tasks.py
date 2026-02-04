
from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from django.conf import settings
from django.db import close_old_connections
from django.core.cache import cache
from django.template.loader import render_to_string
from .google_calendar import get_calendar_service
from .emails import send_appointment_emails, send_contact_emails, send_html_email
from .models import Appointment, Contact
from django.core.mail import send_mail

import logging
logger = logging.getLogger(__name__)

# ---------------------------------------------------
# WELCOME EMAIL TASK
# ---------------------------------------------------
@shared_task(bind=True, max_retries=3)
def send_welcome_email_task(self, user_id, username, email, is_social=False):
    """
    Send welcome email using 'emails/welcome_email.html' template.
    """
    close_old_connections()
    cache_key = f"welcome_email_sent:{user_id}"

    if cache.get(cache_key):
        logger.info(f"[Welcome Email] Already sent for user {user_id}")
        return "skipped"

    try:
        # Context matching variables in welcome_email.html
        context = {
            'username': username,
            'is_social': is_social,
            # If your template needs a specific login URL or other data, add it here
        }

        # Use the helper to render and send
        send_html_email(
            subject='Welcome to OroShine Dental Care! 🦷',
            template_name="emails/welcome_email.html",
            context=context,
            recipient_list=[email]
        )

        cache.set(cache_key, True, 60 * 60 * 24)  # 24 hours
        logger.info(f"[Welcome Email] Successfully sent for user {user_id}")
        return "sent"

    except Exception as e:
        logger.error(f"[Welcome Email] Failed for user {user_id}: {e}")
        raise self.retry(exc=e, countdown=10)


# ---------------------------------------------------
# APPOINTMENT EMAIL TASK
# ---------------------------------------------------

@shared_task(bind=True, max_retries=3)
def send_appointment_email_task(self, appointment_ulid):
    """
    Send User, Admin, and Doctor emails using HTML templates.
    CHANGED: Now uses ULID instead of numeric ID
    """
    close_old_connections()

    cache_key = f"appointment_email_sent:{appointment_ulid}"

    if cache.get(cache_key):
        logger.info(f"[Email] Already sent for appointment {appointment_ulid}")
        return "skipped"

    try:
        # Use ULID for lookup
        appointment = Appointment.objects.select_related('doctor', 'user').get(ulid=appointment_ulid)
        
        # Call logic in emails.py to send all 3 emails (User/Admin/Doctor)
        send_appointment_emails(appointment)

        cache.set(cache_key, True, 60 * 60 * 24)
        logger.info(f"[Email] Successfully sent for appointment {appointment_ulid}")
        return "sent"

    except Appointment.DoesNotExist:
        logger.error(f"Appointment {appointment_ulid} not found")
        return "not_found"
    except Exception as e:
        logger.error(f"Error sending appointment email: {e}")
        raise self.retry(exc=e, countdown=10)






# ---------------------------------------------------
# CONTACT US EMAIL TASK
# ---------------------------------------------------
@shared_task(bind=True, max_retries=3)
def send_contact_email_task(self, contact_id):
    close_old_connections()
    cache_key = f"contact_email_sent:{contact_id}"

    if cache.get(cache_key):
        logger.info("[Contact Email] Skipped (already sent)")
        return "skipped"

    try:
        contact = Contact.objects.get(id=contact_id)

        send_contact_emails({
            "name": contact.name,
            "email": contact.email,
            "subject": contact.subject,
            "message": contact.message,
        })

        cache.set(cache_key, True, 86400)
        logger.info("[Contact Email] Sent for %s", contact.email)
        return "sent"

    except Contact.DoesNotExist:
        return "not_found"

    except Exception as e:
        logger.exception("[Contact Email] Failed")
        raise self.retry(exc=e, countdown=10)


# ---------------------------------------------------
# PASSWORD RESET TASK
# ---------------------------------------------------
@shared_task(bind=True, max_retries=3)
def send_password_reset_email_task(self, email, reset_link, username):
    close_old_connections()

    try:
        send_html_email(
            subject="Reset your OroShine password ",
            template_name="emails/password_reset_email.html",
            context={
                "username": username,
                "reset_link": reset_link,
            },
            recipient_list=[email],
        )
        return "sent"

    except Exception as e:
        logger.exception("[Password Reset] Failed")
        raise self.retry(exc=e, countdown=15)




# ---------------------------------------------------



@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def send_password_reset_success_email_task(self, email, username):
    """
    Sends an HTML confirmation email after a successful password reset.
    Uses the same send_html_email() helper every other task in this file uses
    so styling and error handling are consistent across the board.
    """
    close_old_connections()

    try:
        send_html_email(
            subject="Your OroShine password has been changed ✓",
            template_name="emails/password_reset_success.html",
            context={
                "username": username,
            },
            recipient_list=[email],
        )
        logger.info("[Password Reset Success] Sent to %s", email)
        return "sent"

    except Exception as e:
        logger.exception("[Password Reset Success] Failed for %s", email)
        raise self.retry(exc=e, countdown=15)

# -----------------------------------



# update calender task  as above casuing trouble so little modifications , removed email reminders 

@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def create_calendar_event_task(self, appointment_ulid):
    close_old_connections()

    logger.info("CALENDAR_ID=%s", settings.GOOGLE_CALENDAR_ID)

    try:
        appt = (
            Appointment.objects
            .select_related("doctor")
            .only(
                 "ulid", "date", "time", "name", "email",
                "service", "message", "status",
                "calendar_event_id", "doctor__email"
                 )
                .get(ulid=appointment_ulid)
        )

        # -----------------------------
        # Idempotency
        # -----------------------------
        if appt.calendar_event_id:
            logger.info("[Calendar] Event already exists for %s", appointment_id)
            return {"status": "skipped"}

        if appt.status not in ["confirmed", "pending"]:
            return {"status": "skipped", "reason": appt.status}

        if not appt.doctor or not appt.doctor.email:
            return {"status": "invalid_doctor"}

        # -----------------------------
        # Date & Time
        # -----------------------------
        appt_date = appt.date if not isinstance(appt.date, str) \
            else datetime.strptime(appt.date, "%Y-%m-%d").date()

        appt_time = appt.time
        if isinstance(appt_time, str):
            if len(appt_time.split(":")) == 2:
                appt_time += ":00"
            appt_time = datetime.strptime(appt_time, "%H:%M:%S").time()

        start_dt = timezone.make_aware(
            datetime.combine(appt_date, appt_time),
            timezone.get_current_timezone()
        )
        end_dt = start_dt + timedelta(minutes=30)

        # -----------------------------
        # Google Event (NO attendees)
        # -----------------------------
        event = {
            "summary": f"Dental Appointment – {appt.service} | {appt.name}",
            "description": (
                f"Patient: {appt.name}\n"
                f"Patient Email: {appt.email}\n"
                f"Doctor Email: {appt.doctor.email}\n\n"
                f"Message:\n{appt.message or 'N/A'}"
            ),
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "location": (
                "Sai Dental Clinic, 203, 2nd Floor, Chandrangan Residency Tower, "
                "Above GP Parshik Bank, Diva East, Navi Mumbai"
            ), 
          "attendees": [{"email": appt.email}, 
          {"email": appt.doctor.email},      
          ],
        }
        logger.info("Using calendar: %s", settings.GOOGLE_CALENDAR_ID)
        logger.info("Calendar event payload: %s", event)



        service = get_calendar_service()
        created_event = service.events().insert(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            body=event,
            sendUpdates="all"   
        ).execute()

        Appointment.objects.filter(id=appointment_id).update(
            calendar_event_id=created_event["ulid"]
        )

        logger.info(
            "[Calendar] Event created appointment=%s event=%s",
            appointment_id, created_event["ulid"]
        )

        return {
            "status": "success",
            "event_id": created_event["ulid"],
            "event_link": created_event.get("htmlLink"),
        }

    except Appointment.DoesNotExist:
        return {"status": "not_found"}

    except Exception as exc:
        logger.exception("[Calendar] Failed to create event")
        raise self.retry(exc=exc)

    finally:
        close_old_connections()









@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def send_appointment_cancel_email_task(self, appointment_ulid):
    close_old_connections()
    cache_key = f"appointment_cancel_email_sent:{appointment_ulid}"

    if cache.get(cache_key):
        return "skipped"

    appt = Appointment.objects.select_related("user", "doctor").get(id=appointment_ulid)

    send_mail(
        subject="Your Appointment Has Been Cancelled",
        message=render_to_string(
            "emails/appointment_cancel.txt",
            {
                "user": appt.user,
                "doctor": appt.doctor,
                "date": appt.date,
                "time": appt.get_time_display(),
                "service": appt.get_service_display(),
            },
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[appt.user.email],
    )

    cache.set(cache_key, True, 86400)
    return "sent"

