from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.validators import validate_email, ValidationError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta, time
import logging

from .models import Contact, Appointment, UserProfile, TimeSlot
from .tasks import (
    send_contact_email_task,
    send_appointment_email_task,
    create_calendar_event_task
)
from .forms import NewUserForm, AppointmentForm, UserProfileForm

logger = logging.getLogger(__name__)


# ==========================================
# BASIC PAGES
# ==========================================
def homepage(request):
    return render(request, 'index.html', context={})

def about(request):
    return render(request, 'about.html', context={})

def price(request):
    return render(request, 'price.html', context={})

def service(request):
    return render(request, 'service.html', context={})

from django.shortcuts import render

def team(request):
   
    return render(request, "team.html", context={})


from django.contrib import messages

def newsletter(request):
    if request.method == "POST":
        email = request.POST.get("email")
        # TODO: save to database or send email
        messages.success(request, "Thank you for subscribing!")
    return redirect("home")


def testimonial(request):
    return render(request, 'testimonial.html', context={})


# ==========================================
# AJAX: CHECK AVAILABLE SLOTS
# ==========================================
@require_http_methods(["POST"])
@login_required
def check_available_slots(request):
    """
    AJAX endpoint to check available appointment slots
    Returns available time slots for a given date and doctor
    """
    try:
        date_str = request.POST.get('date')
        doctor_email = request.POST.get('doctor_email')
        
        if not date_str or not doctor_email:
            return JsonResponse({
                'status': 'error',
                'message': 'Date and doctor email are required'
            }, status=400)
        
        # Parse date
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Check if date is in the past
        if appointment_date < timezone.now().date():
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot book appointments in the past'
            }, status=400)
        
        # Get all booked slots for this date and doctor
        booked_appointments = Appointment.objects.filter(
            date=appointment_date,
            doctor_email=doctor_email,
            status__in=['pending', 'confirmed']
        ).values_list('time', flat=True)
        
        # Convert to set for faster lookup
        booked_times = set(booked_appointments)
        
        # Get all possible time slots
        all_slots = TimeSlot.objects.filter(is_active=True).order_by('time')
        
        # Build available slots
        available_slots = []
        current_time = timezone.now().time()
        is_today = appointment_date == timezone.now().date()
        
        for slot in all_slots:
            # Skip past slots if it's today
            if is_today and slot.time <= current_time:
                continue
            
            # Check if slot is available
            is_available = slot.time not in booked_times
            
            available_slots.append({
                'time': slot.time.strftime('%H:%M'),
                'display_time': slot.time.strftime('%I:%M %p'),
                'is_available': is_available
            })
        
        return JsonResponse({
            'status': 'success',
            'date': date_str,
            'slots': available_slots,
            'total_slots': len(available_slots),
            'available_count': sum(1 for s in available_slots if s['is_available'])
        })
    
    except ValueError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid date format. Use YYYY-MM-DD'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error checking available slots: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while checking availability'
        }, status=500)


# ==========================================
# AJAX: BOOK APPOINTMENT
# ==========================================
@require_http_methods(["POST"])
@login_required
def book_appointment_ajax(request):
    """
    AJAX endpoint for booking appointments
    Provides instant feedback with UX optimization
    """
    try:
        form = AppointmentForm(request.POST)
        
        if not form.is_valid():
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid form data',
                'errors': form.errors
            }, status=400)
        
        appointment_obj = form.save(commit=False)
        appointment_obj.user = request.user
        
        # Use user's profile data if available
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            if not appointment_obj.phone and profile.phone:
                appointment_obj.phone = profile.phone
        
        # Check for conflicts with buffer
        buffer_minutes = 15
        appointment_datetime = datetime.combine(appointment_obj.date, appointment_obj.time)
        start_time = (appointment_datetime - timedelta(minutes=buffer_minutes)).time()
        end_time = (appointment_datetime + timedelta(minutes=buffer_minutes)).time()
        
        # Optimized query with select_related
        conflicting_appointment = Appointment.objects.filter(
            date=appointment_obj.date,
            doctor_email=appointment_obj.doctor_email,
            time__range=(start_time, end_time),
            status__in=['pending', 'confirmed']
        ).select_related('user').first()
        
        if conflicting_appointment:
            return JsonResponse({
                'status': 'error',
                'message': f'This time slot is already booked (±{buffer_minutes} min buffer)',
                'booked_time': conflicting_appointment.time.strftime('%I:%M %p')
            }, status=409)
        
        # Save appointment
        appointment_obj.save()
        
        # Queue background tasks (non-blocking)
        send_appointment_email_task.delay(appointment_obj.id)
        create_calendar_event_task.delay(appointment_obj.id)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Appointment booked successfully! Confirmation email will arrive shortly.',
            'appointment': {
                'id': appointment_obj.id,
                'service': appointment_obj.get_service_display(),
                'date': appointment_obj.date.strftime('%B %d, %Y'),
                'time': appointment_obj.time.strftime('%I:%M %p'),
                'doctor': appointment_obj.doctor_email,
                'status': appointment_obj.get_status_display()
            }
        }, status=201)
    
    except Exception as e:
        logger.error(f"Error booking appointment: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again.'
        }, status=500)


# ==========================================
# APPOINTMENT VIEW (Standard + AJAX)
# ==========================================
@login_required(login_url='/login/')
def appointment(request):
    """
    Main appointment view - supports both standard and AJAX requests
    """
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return book_appointment_ajax(request)
        
        # Standard form submission (fallback)
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment_obj = form.save(commit=False)
            appointment_obj.user = request.user
            appointment_obj.save()
            
            # Queue tasks
            send_appointment_email_task.delay(appointment_obj.id)
            create_calendar_event_task.delay(appointment_obj.id)
            
            messages.success(request, "Appointment booked successfully!")
            return redirect('appointment')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AppointmentForm()
    
    # Get user's upcoming appointments with optimization
    upcoming_appointments = Appointment.objects.filter(
        user=request.user,
        date__gte=timezone.now().date(),
        status__in=['pending', 'confirmed']
    ).select_related('user').order_by('date', 'time')[:5]
    
    context = {
        'form': form,
        'upcoming_appointments': upcoming_appointments,
        'doctors': [
            {'email': 'dr.smith@oroshine.com', 'name': 'Dr. Sarah Smith'},
            {'email': 'dr.johnson@oroshine.com', 'name': 'Dr. Michael Johnson'},
            {'email': 'dr.patel@oroshine.com', 'name': 'Dr. Priya Patel'},
        ]
    }
    
    return render(request, 'appointment.html', context)


# ==========================================
# AJAX: LOGIN
# ==========================================
@require_http_methods(["POST"])
def login_ajax(request):
    """
    AJAX login endpoint for seamless authentication
    """
    try:
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Username and password are required'
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Get user profile data
            profile_data = {}
            if hasattr(user, 'profile'):
                profile_data = {
                    'phone': user.profile.phone,
                    'avatar': user.profile.avatar.url if user.profile.avatar else None
                }
            
            return JsonResponse({
                'status': 'success',
                'message': f'Welcome back, {user.first_name or user.username}!',
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile': profile_data
                },
                'redirect_url': request.GET.get('next', '/')
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username or password'
            }, status=401)
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred during login'
        }, status=500)


# ==========================================
# CONTACT VIEW
# ==========================================
def contact(request):
    if request.method == 'GET':
        return render(request, 'contact.html', {'page_title': 'Contact Us - OroShine Dental Care'})

    # Check authentication
    if not request.user.is_authenticated:
        messages.error(request, "Please login to submit the contact form.")
        return redirect('login')

    # Extract form data
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip().lower()
    subject = request.POST.get('subject', '').strip()
    message_text = request.POST.get('message', '').strip()

    # Validation
    errors = []
    if not name: errors.append("Name is required")
    if not email:
        errors.append("Email is required")
    else:
        try: 
            validate_email(email)
        except ValidationError: 
            errors.append("Invalid email address")
    if not subject: errors.append("Subject is required")
    if not message_text: errors.append("Message is required")

    if errors:
        for error in errors: 
            messages.error(request, error)
        return render(request, 'contact.html', {
            'page_title': 'Contact Us - OroShine Dental Care',
            'name': name, 'email': email, 'subject': subject, 'message': message_text
        })

    # Save inquiry
    contact_inquiry = Contact.objects.create(
        user=request.user,
        name=name, 
        email=email, 
        subject=subject, 
        message=message_text
    )

    # Queue async email task
    send_contact_email_task.delay(
        contact_inquiry.id,
        request.META.get("REMOTE_ADDR", "Unknown IP")
    )

    messages.success(request, "Thank you! We've received your message and will respond within 24 hours.")
    return redirect('home')


# ==========================================
# USER PROFILE
# ==========================================
@login_required
def user_profile(request):
    """
    User profile view with edit capability
    """
    profile = request.user.profile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('user_profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=profile)
    
    # Get user's appointment history with optimization
    appointments = Appointment.objects.filter(
        user=request.user
    ).select_related('user').order_by('-date', '-time')
    
    # Paginate appointments
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get contact history
    contacts = Contact.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    context = {
        'form': form,
        'profile': profile,
        'appointments': page_obj,
        'contacts': contacts,
        'total_appointments': appointments.count(),
        'pending_appointments': appointments.filter(status='pending').count(),
        'completed_appointments': appointments.filter(status='completed').count(),
    }
    
    return render(request, 'profile.html', context)


# ==========================================
# AUTHENTICATION VIEWS
# ==========================================
def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. Welcome!")
            return redirect("/")
        messages.error(request, "Registration failed. Please check the information provided.")
    else:
        form = NewUserForm()
    return render(request, "register.html", {"register_form": form})


def login_request(request):
    """
    Standard login view with AJAX support
    """
    # Handle AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return login_ajax(request)
    
    # Standard form submission
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect(request.GET.get('next', '/'))
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, "login.html", {"login_form": form})


def logout_request(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("/")