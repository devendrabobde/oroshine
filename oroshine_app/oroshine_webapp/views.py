from django.shortcuts import render, redirect
from .forms import NewUserForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib import messages
from django.core.mail import send_mail
from .models import Contact, Appointment
from .forms import NewUserForm, AppointmentForm
from .utils import create_nocodeapi_event, send_contact_form_emails
from django.utils.timezone import now
from django.core.validators import validate_email, ValidationError
from datetime import datetime, timedelta, date
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .emails import send_appointment_email
import requests
import logging

logger = logging.getLogger(__name__)


def homepage(request):
    return render(request, 'index.html', context={})

def about(request):
    return render(request, 'about.html', context={})



def appointment(request):
    """
    Handles appointment booking with enhanced slot conflict detection and user-friendly messages.
    """
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment_obj = form.save(commit=False)
            appointment_time = appointment_obj.time
            buffer_minutes = 30

            # Calculate time buffer range
            appointment_datetime = datetime.combine(appointment_obj.date, appointment_time)
            start_time = (appointment_datetime - timedelta(minutes=buffer_minutes)).time()
            end_time = (appointment_datetime + timedelta(minutes=buffer_minutes)).time()

            # Check for overlapping appointments
            is_booked = Appointment.objects.filter(
                date=appointment_obj.date,
                doctor_email=appointment_obj.doctor_email,
                time__range=(start_time, end_time)
            ).exists()

            logger.info(
                f"Checking availability for {appointment_obj.date} "
                f"{start_time}–{end_time} with {appointment_obj.doctor_email}: {is_booked}"
            )

            if is_booked:
                messages.error(
                    request,
                    f" This time slot or a nearby slot is already booked "
                    f"(±{buffer_minutes} minutes). Please choose another one."
                )
                return render(request, 'appointment.html', {'form': form})

            try:
                # Save appointment
                appointment_obj.save()
                logger.info(f"Appointment saved: {appointment_obj}")

                # Send confirmation email
                send_appointment_email(appointment_obj)

                # Create calendar event
                calendar_response = create_nocodeapi_event(appointment_obj)
                logger.info(f"Calendar API Response: {calendar_response}")

                messages.success(
                    request,
                    " Appointment booked successfully! A confirmation email and calendar invite have been sent."
                )
                return redirect('appointment')

            except Exception as e:
                logger.exception("Error booking appointment")
                messages.error(
                    request,
                    f" There was an issue booking your appointment: {str(e)}"
                )
        else:
            messages.warning(
                request,
                "Please fix the highlighted errors before submitting the form."
            )
    else:
        form = AppointmentForm()

    return render(request, 'appointment.html', {'form': form})








def contact(request):
    """
    Handles the contact form submission, validation, and saves the inquiry.
    It then delegates the email sending to a separate service.
    """
    if request.method == 'GET':
        return render(request, 'contact.html', {
            'page_title': 'Contact Us - OroShine Dental Care'
        })

    try:
        # Extract and sanitize form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        # Validation
        errors = []
        if not name:
            errors.append("Name is required")
        if not email:
            errors.append("Email is required")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("Invalid email address")
        if not subject:
            errors.append("Subject is required")
        if not message:
            errors.append("Message is required")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'contact.html', {
                'page_title': 'Contact Us - OroShine Dental Care',
                'name': name,
                'email': email,
                'subject': subject,
                'message': message
            })

        # Save to database
        contact_inquiry = Contact.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        # Get request-specific metadata
        user_ip = request.META.get('REMOTE_ADDR', 'Unknown IP')
        page_origin = request.META.get('HTTP_REFERER', 'Direct Access')
        timestamp = now().strftime('%B %d, %Y at %I:%M %p %Z')

        # Delegate email sending to a service function
        send_contact_form_emails(contact_inquiry, user_ip, page_origin, timestamp)

        messages.success(request, " Thank you! We've received your message and will contact you within 24 hours.")
        return redirect('home')

    except Exception as e:
        logger.error(f"Contact form error: {str(e)}", exc_info=True)
        messages.error(request, "Something went wrong. Please try again.")
        return redirect('contact')


def price(request):
    return render(request, 'price.html', context={})

def service(request):
    return render(request, 'service.html', context={})

def team(request):
    return render(request, 'team.html', context={})

def testimonial(request):
    return render(request, 'testimonial.html', context={})

def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("/")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()
    return render(request=request, template_name="register.html", context={"register_form": form})

def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"You are now logged in as {username}.")
                messages.success(request, "Login successful.")
                return redirect("/")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request=request, template_name="login.html", context={"login_form": form})

def logout_request(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("/")





# def create_nocodeapi_event(appointment):
#     """
#     Creates a Google Calendar event using NoCodeAPI.
#     """
#     try:
#         url = f"{settings.NOCODEAPI_BASE_URL}/event"
#         start_datetime = datetime.combine(appointment.date, appointment.time)
#         end_datetime = start_datetime + timedelta(minutes=30)
        
#         payload = {
#             "summary": f"Dental Appointment: {appointment.service}",
#             "description": f"""
# Appointment Details:
# - Service: {appointment.service}
# - Patient: {appointment.name}
# - Patient Email: {appointment.email}
# - Doctor: {appointment.doctor_email}
# - Additional Notes: {appointment.message or "None"}
#             """.strip(),
#             "start": {
#                 "dateTime": start_datetime.isoformat(),
#                 "timeZone": "Asia/Kolkata"
#             },
#             "end": {
#                 "dateTime": end_datetime.isoformat(),
#                 "timeZone": "Asia/Kolkata"
#             },
#             "attendees": [
#                 {"email": appointment.email},
#                 {"email": appointment.doctor_email}
#             ],
#         }

#         headers = {"Content-Type": "application/json"}

#         response = requests.post(url, json=payload, headers=headers, timeout=10)
#         response.raise_for_status()
        
#         return response.json()
    
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Calendar API request failed: {e}")
#         raise Exception(f"Calendar API request failed: {e}")
#     except Exception as e:
#         logger.error(f"Unexpected error creating calendar event: {e}")
#         raise