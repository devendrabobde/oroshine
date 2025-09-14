from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.utils.timezone import now
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView

from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm, 
    ProfileUpdateForm,
    ContactForm, 
    AppointmentForm,
    CustomPasswordResetForm
)
from .models import (
    CustomUser, 
    UserProfile, 
    Contact,
    Appointment
)

from .emails import (
    send_appointment_email,
    send_registration_email,
    send_contact_form_emails,
)
from .utils import create_nocodeapi_event
import logging
logger = logging.getLogger(__name__)


# Custom authentication backend for email login
class EmailBackend:
    """
    Custom authentication backend that allows users to log in using their email address.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find user by email
            user = CustomUser.objects.get(email=username.lower())
        except CustomUser.DoesNotExist:
            # Try to find user by username as fallback
            try:
                user = CustomUser.objects.get(username=username.lower())
            except CustomUser.DoesNotExist:
                return None
        
        # Check password
        if user.check_password(password) and user.is_active:
            return user
        return None
    
    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None


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
        appointment_obj.user = request.user  # Link to current user
        
        appointment_datetime = datetime.combine(
            appointment_obj.date, appointment_obj.time
        )
        buffer_minutes = 30
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
            return redirect('/appointment')
        except Exception as e:
            logger.exception("Error while booking appointment")
            messages.error(request, "Unexpected error. Please try again later.")

    else:
        # Pre-populate form with user data
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': f"{request.user.first_name} {request.user.last_name}".strip(),
                'email': request.user.email,
            }
        form = AppointmentForm(initial=initial_data)

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
        return redirect('contact')
    except Exception:
        logger.exception("Contact form submission failed")
        messages.error(request, "Something went wrong. Please try again.")
        return redirect('contact')


# ------------------ AUTHENTICATION ------------------ #
@csrf_protect
@never_cache
@transaction.atomic
def register_request(request):
    """Enhanced user registration with atomic transaction"""
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('home')
    
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user
                    user = form.save(commit=False)
                    user.email = user.email.lower()
                    user.username = user.username.lower()
                    user.save()
                    
                    # Create profile with additional data
                    profile_data = {
                        'dob': form.cleaned_data.get('dob'),
                        'gender': form.cleaned_data.get('gender'),
                        'address': form.cleaned_data.get('address'),
                        'emergency_contact_name': form.cleaned_data.get('emergency_contact_name'),
                        'emergency_contact_number': form.cleaned_data.get('emergency_contact_number'),
                    }
                    
                    UserProfile.objects.create(user=user, **profile_data)
                    
                    # Log the user in
                    login(request, user, backend="allauth.account.auth_backends.AuthenticationBackend")
                    
                    # Send welcome email
                    try:
                        send_registration_email(user)
                    except Exception as e:
                        logger.error(f"Failed to send registration email to {user.email}: {e}")
                    
                    logger.info(f"New user registered: {user.username} ({user.email})")
                    messages.success(request, f"Welcome {user.first_name}! Your account has been created successfully.")
                    
                    return redirect('home')
                    
            except IntegrityError as e:
                logger.error(f"Registration failed due to integrity error: {e}")
                messages.error(request, "Registration failed. Please try again.")
            except Exception as e:
                logger.error(f"Unexpected error during registration: {e}")
                messages.error(request, "An unexpected error occurred. Please try again.")
        else:
            logger.warning(f"Registration form validation failed: {form.errors}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, "register.html", {"register_form": form})


@csrf_protect
@never_cache
def login_request(request):
    """Enhanced login view with email-based authentication"""
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('home')

    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email_or_username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Use custom authentication
            user = authenticate(request, username=email_or_username, password=password)
            
            if user is not None:
                login(request, user, backend="allauth.account.auth_backends.AuthenticationBackend")

                # Handle remember me
                if not remember_me:
                    request.session.set_expiry(0)  # Browser session
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                logger.info(f"User logged in: {user.username} ({user.email})")
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")

                # Redirect to next page or home
                next_page = request.GET.get('next', 'home')
                return redirect(next_page)
            else:
                logger.warning(f"Login failed for: {email_or_username}")
                messages.error(request, "Invalid email/username or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomAuthenticationForm()

    return render(request, "login.html", {
        "login_form": form,
        "title": "Login"
    })


@login_required
def logout_request(request):
    """Enhanced logout with better messaging"""
    user_name = request.user.first_name or request.user.username
    logout(request)
    messages.success(request, f"Goodbye {user_name}! You have successfully logged out.")
    return redirect("/")


# ------------------ PROFILE MANAGEMENT ------------------ #
@login_required
@csrf_protect
def profile_view(request):
    """User profile view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user': request.user,
        'profile': profile,
        'title': 'My Profile'
    }
    
    return render(request, 'profile/profile_page.html', context)


@login_required
@csrf_protect
@transaction.atomic
def profile_update(request):
    """Update user profile"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update user fields
                    request.user.first_name = form.cleaned_data['first_name']
                    request.user.last_name = form.cleaned_data['last_name']
                    request.user.email = form.cleaned_data['email'].lower()
                    request.user.phone_number = form.cleaned_data.get('phone_number', '')
                    request.user.save()
                    
                    # Update profile
                    form.save()
                    
                    logger.info(f"Profile updated for user: {request.user.username}")
                    messages.success(request, "Profile updated successfully!")
                    return redirect('profile')
                    
            except Exception as e:
                logger.error(f"Profile update failed for {request.user.username}: {e}")
                messages.error(request, "Failed to update profile. Please try again.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileUpdateForm(instance=profile, user=request.user)
    
    return render(request, 'registration/profile_update.html', {
        'form': form,
        'title': 'Update Profile'
    })


@login_required
def appointment_list(request):
    """List user appointments"""
    appointments = Appointment.objects.filter(user=request.user).order_by('-date', '-time')
    
    return render(request, 'appointment/list.html', {
        'appointments': appointments,
        'title': 'My Appointments'
    })


def appointment_success(request):
    """Appointment success page"""
    return render(request, 'appointment/success.html', {
        'title': 'Appointment Booked'
    })


# ------------------ AJAX VIEWS ------------------ #
def check_email_availability(request):
    """AJAX view to check email availability"""
    if request.method == 'GET':
        email = request.GET.get('email', '').lower().strip()
        if email:
            is_available = not CustomUser.objects.filter(email=email).exists()
            return JsonResponse({'available': is_available})
    return JsonResponse({'available': False})


# ------------------ CLASS-BASED VIEWS ------------------ #
class CustomPasswordResetView(PasswordResetView):
    """Enhanced password reset view"""
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        logger.info(f"Password reset requested for: {form.cleaned_data.get('email')}")
        return super().form_valid(form)


# ------------------ SOCIAL AUTH SUCCESS HANDLER ------------------ #
def social_auth_success(request):
    """Handle successful social authentication"""
    if request.user.is_authenticated:
        # Ensure profile exists
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Send welcome email for new social auth users
        if created:
            try:
                send_registration_email(request.user)
                logger.info(f"Welcome email sent to new social user: {request.user.email}")
            except Exception as e:
                logger.error(f"Failed to send social auth welcome email: {e}")
        
        logger.info(f"Social auth login: {request.user.username} ({request.user.email})")
        messages.success(request, f"Welcome {request.user.first_name or request.user.username}!")
        
    return redirect('home')