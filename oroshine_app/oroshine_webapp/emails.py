
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import datetime
import logging
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.timezone import now



logger = logging.getLogger(__name__)



def send_registration_email(user):
    """
    Sends a branded welcome email to the user after successful registration.
    """
    subject = "Welcome to Oroshine Dental Care!"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user.email]

    # Render the email template with current date/time
    html_content = render_to_string("registration_welcome.html", {
        "user": user,
        "now": now()
    })
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    email.attach_alternative(html_content, "text/html")
    email.send()





logger = logging.getLogger(__name__)

def send_contact_form_emails(contact_inquiry, user_ip, page_origin, timestamp):
    """
    Sends confirmation emails to both the user and the admin.
    """
    try:
        # Render User Email
        html_content_user = render_to_string(
            'contact_email_template.html',
            {
                'name': contact_inquiry.name,
                'subject': contact_inquiry.subject,
                'message': contact_inquiry.message,
                'timestamp': timestamp,
            },
            using=None
        )

        text_content_user = f"""
        Dear {contact_inquiry.name},

        Thank you for contacting OroShine Dental Care!

        Subject: {contact_inquiry.subject}
        Message: {contact_inquiry.message}
        Submitted on: {timestamp}

        This is an automated email. Do not reply.
        """

        email_user = EmailMultiAlternatives(
            subject="✨ Thank You for Contacting OroShine Dental Care",
            body=text_content_user,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact_inquiry.email]
        )
        email_user.attach_alternative(html_content_user, "text/html")
        email_user.send(fail_silently=True)

        # Render Admin Email
        html_content_admin = render_to_string(
            'contact_email_template.html',
            {
                'name': contact_inquiry.name,
                'email': contact_inquiry.email,
                'subject': contact_inquiry.subject,
                'message': contact_inquiry.message,
                'timestamp': timestamp,
                'user_ip': user_ip,
                'page_origin': page_origin,
            }
        )

        text_content_admin = f"""
        NEW CONTACT FORM SUBMISSION

        Name: {contact_inquiry.name}
        Email: {contact_inquiry.email}
        Subject: {contact_inquiry.subject}
        Message: {contact_inquiry.message}
        IP: {user_ip}
        Origin: {page_origin}
        Submitted on: {timestamp}
        """

        admin_recipients = [settings.EMAIL_HOST_USER, "admin1@example.com", "admin2@example.com"]

        email_admin = EmailMultiAlternatives(
            subject=f"🚨 New Contact Inquiry - {contact_inquiry.name} ({contact_inquiry.subject})",
            body=text_content_admin,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_recipients,
            reply_to=[contact_inquiry.email]
        )
        email_admin.attach_alternative(html_content_admin, "text/html")
        email_admin.send(fail_silently=True)

    except Exception as e:
        logger.error(f"Failed to send contact form emails: {e}", exc_info=True)




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