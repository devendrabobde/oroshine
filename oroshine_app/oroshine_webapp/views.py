from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.validators import validate_email, ValidationError
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseBadRequest
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from .forms import NewUserForm, AppointmentForm,UserProfileForm
from .models import Contact, Appointment, UserProfile
from django.db import IntegrityError
from .utils import create_nocodeapi_event
from .emails import (
    send_appointment_email,
    send_registration_email,
    send_contact_form_emails,
    send_welcome_login_email
)
from django.http import JsonResponse
from django.contrib.auth import get_user_model
User = get_user_model()


import logging
logger = logging.getLogger(__name__)


# ------------------ STATIC PAGES ------------------ #
def homepage(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def price(request):
    return render(request, 'price.html')

def service(request):
    return render(request, 'service.html')

def team(request):
    return render(request, 'team.html')

def testimonial(request):
    return render(request, 'testimonial.html')



# ------------------ USER PROFILE ------------------ #

@login_required(login_url='/login')
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            # Update related profile fields
            profile.dob = request.POST.get('dob')
            profile.gender = request.POST.get('gender')
            profile.address = request.POST.get('address')
            profile.phone_number = request.POST.get('phone_number')
            profile.emergency_contact_name = request.POST.get('emergency_contact_name')
            profile.emergency_contact_number = request.POST.get('emergency_contact_number')
            profile.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        # Pre-fill form with User + Profile data
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'username': request.user.username,
            'dob': profile.dob,
            'gender': profile.gender,
            'address': profile.address,
            'phone_number': profile.phone_number,
            'emergency_contact_name': profile.emergency_contact_name,
            'emergency_contact_number': profile.emergency_contact_number,
        }
        form = UserProfileForm(initial=initial_data)

    return render(request, 'profile.html', {'form': form, 'profile': profile})


# ------------------ APPOINTMENT ------------------ #
@login_required(login_url='/login')
@csrf_protect
@require_http_methods(["GET", "POST"])
def appointment(request):
    """
    Handles appointment booking with improved slot conflict detection,
    CSRF protection, and better error handling.
    """
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if not form.is_valid():
            messages.warning(request, "Please correct the highlighted errors.")
            return render(request, 'appointment.html', {'form': form})

        appointment_obj = form.save(commit=False)
        appointment_datetime = datetime.combine(
            appointment_obj.date, appointment_obj.time
        )
        buffer_minutes = 15
        start_dt = appointment_datetime - timedelta(minutes=buffer_minutes)
        end_dt = appointment_datetime + timedelta(minutes=buffer_minutes)
        
        is_booked = Appointment.objects.filter(
            doctor_email=appointment_obj.doctor_email,
            date=appointment_obj.date,
            
            time__range=(start_dt.time(), end_dt.time())
        ).exists()

        if is_booked:
            messages.error(
                request,
                f"Time slot already booked (±{buffer_minutes} min). Please choose another."
            )
            return render(request, 'appointment.html', {'form': form})

        try:
            appointment_obj.save()
            logger.info(f"Appointment booked: {appointment_obj}")

            # Send confirmation email 
            send_appointment_email(appointment_obj)

            # Add to calendar
            create_nocodeapi_event(appointment_obj)

            messages.success(
                request,
                "Appointment booked successfully! Confirmation email sent."
            )
            return redirect('appointment')
        except Exception:
            logger.exception("Error while booking appointment")
            messages.error(request, "Unexpected error. Please try again later.")

    else:
        form = AppointmentForm()

    return render(request, 'appointment.html', {'form': form})


# ------------------ CONTACT FORM ------------------ #

@csrf_protect
@require_http_methods(["GET", "POST"])
def contact(request):
    """
    Secure contact form handling with CSRF protection, email validation,
    spam protection potential, and logging.
    """
    if request.method == 'GET':
        return render(request, 'contact.html', {'page_title': 'Contact Us - OroShine Dental Care'})

    # POST: Process submission
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip().lower()
    subject = request.POST.get('subject', '').strip()
    message = request.POST.get('message', '').strip()

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

    try:
        # Save inquiry
        contact_inquiry = Contact.objects.create(
            name=name, email=email, subject=subject, message=message
        )

        user_ip = request.META.get('REMOTE_ADDR', 'Unknown IP')
        page_origin = request.META.get('HTTP_REFERER', 'Direct Access')
        timestamp = now().strftime('%B %d, %Y at %I:%M %p %Z')

        # Send confirmation email
        send_contact_form_emails(contact_inquiry, user_ip, page_origin, timestamp)

        messages.success(request, "Thank you! We'll respond within 24 hours.")
        return redirect('contact')  # Keeps user on the same page
    except Exception:
        logger.exception("Contact form submission failed")
        messages.error(request, "Something went wrong. Please try again.")
        return redirect('contact')




# ------------------ AUTHENTICATION ------------------ #

def check_email_availability(request):
    email = request.GET.get("email")
    if not email:
        return JsonResponse({"available": False, "message": "Email is required."})

    exists = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({
        "available": not exists,
        "message": "Email available." if not exists else "Email already registered."
    })


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")

            # Enforce unique email
            if User.objects.filter(email__iexact=email).exists():
                messages.error(request, "This email is already registered. Please log in instead.")
                return render(request, "register.html", {"register_form": form})

            try:
                user = form.save()
                # Explicitly login with ModelBackend (normal signup)
                login(
                    request,
                    user,
                    backend='django.contrib.auth.backends.ModelBackend'
                )
                send_registration_email(user)
                messages.success(request, "Registration successful. Welcome email sent!")
                return redirect("/")
            except IntegrityError:
                messages.error(request, "A user with this email already exists.")
        else:
            messages.error(request, "Invalid information. Please correct the errors.")
    else:
        form = NewUserForm()

    return render(request, "register.html", {"register_form": form})




@csrf_protect
def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data.get('username'),
                password=form.cleaned_data.get('password')
            )
            if user:
                login(
                    request,
                    user,
                    backend='django.contrib.auth.backends.ModelBackend'
                )
                messages.success(request, f"Welcome back, {user.username}!")
                if user.email:
                    send_welcome_login_email(user)
                return redirect("/")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid login credentials.")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"login_form": form})
@login_required
def logout_request(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("/")