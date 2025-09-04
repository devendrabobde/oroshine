
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import datetime
import logging
from django.core.mail import EmailMultiAlternatives, get_connection

logger = logging.getLogger(__name__)

def send_appointment_email(appointment, subject="Appointment Booked", template_name="appointment_confirmation.html"):
    """
    Sends a dynamic email with appointment details using Gmail SMTP.
    Template path: oroshine/oroshine_app/templates/appointment_confirmation.html
    """
    context = {
        'appointment': appointment,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    recipient_list = [appointment.email, appointment.doctor_email]

    try:
        print(f"Preparing to send email to: {recipient_list} with subject: '{subject}'")
        logger.info(f"Preparing email to: {recipient_list}")

        # Create and send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            to=recipient_list
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        print(f"Email sent successfully to {recipient_list}")
        logger.info(f"Email sent to {recipient_list}")

    except Exception as e:
        print(f"Failed to send email: {e}")
        logger.error(f"Error sending email: {e}")
        raise Exception(f"Failed to send email: {e}")

    """
    Sends a dynamic email with appointment details using Gmail SMTP.
    Template path: oroshine/oroshine_app/templates/appointment_confirmation.html
    """
    context = {
        'appointment': appointment,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    recipient_list = [appointment.email, appointment.doctor_email]

    try:
        print(f"Preparing to send email to: {recipient_list} with subject: '{subject}'")
        logger.info(f"Preparing email to: {recipient_list}")

        # Debug SMTP connection
        with get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
        ) as connection:
            print("SMTP connection established")
            logger.info("SMTP connection established")

            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)

        print(f"Email sent successfully to {recipient_list}")
        logger.info(f"Email sent to {recipient_list}")

    except Exception as e:
        print(f"Failed to send email: {e}")
        logger.error(f"Error sending email: {e}")
        raise Exception(f"Failed to send email: {e}")