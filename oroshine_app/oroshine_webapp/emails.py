# appointments/emails.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_appointment_emails(appointment):
    """
    Sends admin + user emails.
    Pure email logic only.
    """

    context = {
        "appointment": appointment,
        "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # ======================
    # ADMIN EMAIL
    # ======================
    admin_html = render_to_string(
        "emails/appointment_admin.html", context
    )
    admin_text = strip_tags(admin_html)

    admin_msg = EmailMultiAlternatives(
        subject="New Appointment Booking - OroShine Dental Care",
        body=admin_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_EMAIL],
    )
    admin_msg.attach_alternative(admin_html, "text/html")
    admin_msg.send()

    # ======================
    # USER EMAIL
    # ======================
    user_html = render_to_string(
        "emails/appointment_user.html", context
    )
    user_text = strip_tags(user_html)

    user_msg = EmailMultiAlternatives(
        subject="Your Appointment Confirmation - OroShine Dental Care",
        body=user_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[appointment.email],
    )
    user_msg.attach_alternative(user_html, "text/html")
    user_msg.send()

    logger.info(
        f"Emails sent for appointment {appointment.id}"
    )
