import logging
from datetime import datetime
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


# ------------------------------------------
# SEND APPOINTMENT EMAILS (ADMIN + USER)
# ------------------------------------------
def send_appointment_emails(appointment):
    context = {
        "appointment": appointment,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # -------------------- ADMIN EMAIL --------------------
    admin_html = render_to_string("emails/appointment_admin.html", context)
    admin_text = strip_tags(admin_html)

    admin_msg = EmailMultiAlternatives(
        subject="New Appointment Booking - OroShine Dental Care",
        body=admin_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=["admin@oroshineclinic.com"],
    )
    admin_msg.attach_alternative(admin_html, "text/html")
    admin_msg.send()

    # -------------------- USER EMAIL ---------------------
    user_html = render_to_string("emails/appointment_user.html", context)
    user_text = strip_tags(user_html)

    user_msg = EmailMultiAlternatives(
        subject="Your Appointment Confirmation - OroShine Dental Care",
        body=user_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[appointment.email],
    )
    user_msg.attach_alternative(user_html, "text/html")
    user_msg.send()

    logger.info("Appointment emails sent successfully")


# ------------------------------------------
# SEND CONTACT FORM EMAILS
# ------------------------------------------
def send_contact_emails(contact, user_ip):
    context = {
        "name": contact.name,
        "email": contact.email,
        "subject": contact.subject,
        "message": contact.message,
        "ip": user_ip,
    }

    # -------------------- ADMIN EMAIL --------------------
    admin_html = render_to_string("emails/contact_admin.html", context)
    admin_text = strip_tags(admin_html)

    admin_msg = EmailMultiAlternatives(
        subject=f"📩 New Contact Form Submission — {contact.name}",
        body=admin_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_EMAIL],
    )
    admin_msg.attach_alternative(admin_html, "text/html")
    admin_msg.send()

    # -------------------- USER EMAIL ---------------------
    user_html = render_to_string("emails/contact_user.html", context)
    user_text = strip_tags(user_html)

    user_msg = EmailMultiAlternatives(
        subject="Thank You for Contacting OroShine Dental Clinic",
        body=user_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[contact.email],
    )
    user_msg.attach_alternative(user_html, "text/html")
    user_msg.send()

    logger.info("Contact form emails sent successfully")
