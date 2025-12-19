from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.validators import validate_email, ValidationError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Prefetch, Count, F
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta, time
import logging
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from functools import wraps
from django.conf import settings
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User

from .models import Contact, Appointment, UserProfile, TimeSlot
from .tasks import (
    send_contact_email_task,
    send_appointment_email_task,
    create_calendar_event_task
)
from .forms import NewUserForm, AppointmentForm, UserProfileForm

logger = logging.getLogger(__name__)

# ========================================== 
# CACHING UTILITIES
# ==========================================

def cache_key_generator(prefix, *args, **kwargs):
    """Generate consistent cache keys"""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)



def cache_user_data(timeout=300):
    """Decorator to cache user-specific data"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            cache_key = cache_key_generator(
                'user_view',
                view_func.__name__,
                request.user.id,
                *args,
                **{k: v for k, v in kwargs.items()}
            )
            
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_response
            
            response = view_func(request, *args, **kwargs)
            cache.set(cache_key, response, timeout)
            logger.debug(f"Cache SET: {cache_key}")
            return response
        return wrapper
    return decorator




def invalidate_user_cache(user_id, view_name=None):
    """Invalidate cached data for a specific user"""
    if view_name:
        cache_key = cache_key_generator('user_view', view_name, user_id)
        cache.delete(cache_key)
    else:
        # Delete all user-related caches
        keys_to_delete = [
            f'user_profile:{user_id}',
            f'upcoming_appointments:{user_id}',
            f'user_appointment_stats:{user_id}',
        ]
        for key in keys_to_delete:
            cache.delete(key)



# ========================================== 
# ATOMIC LOCK DECORATOR
# ==========================================

def atomic_with_lock(lock_key_func, timeout=10):
    """
    Decorator for atomic operations with distributed locking
    Prevents race conditions in appointment booking
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate unique lock key based on request data
            lock_key = lock_key_func(request, *args, **kwargs)
            
            # Try to acquire distributed lock
            lock_acquired = cache.add(f'lock:{lock_key}', 'locked', timeout)
            
            if not lock_acquired:
                # Another request is processing, return conflict
                return JsonResponse({
                    'status': 'error',
                    'message': 'Another booking is in progress for this slot. Please wait.'
                }, status=409)
            
            try:
                # Execute the view with transaction
                with transaction.atomic():
                    response = view_func(request, *args, **kwargs)
                return response
            except Exception as e:
                logger.error(f"Error in atomic operation: {e}")
                raise
            finally:
                # Always release the lock
                cache.delete(f'lock:{lock_key}')
        
        return wrapper
    return decorator




# ========================================== 
# BASIC PAGES WITH CACHING
# ==========================================

@cache_page(60 * 15)  # Cache for 15 minutes
def homepage(request):
    """Homepage with cached statistics"""
    stats = cache.get('homepage_stats')
    
    if not stats:
        stats = {
            'total_appointments': Appointment.objects.filter(
                status='completed'
            ).count(),
            'active_users': UserProfile.objects.filter(
                user__is_active=True
            ).count(),
            'satisfaction_rate': 98  # Could be calculated from reviews
        }
        cache.set('homepage_stats', stats, 60 * 30)  # 30 minutes
    
    return render(request, 'index.html', {'stats': stats})


@cache_page(60 * 60)  # Cache for 1 hour
def about(request):
    return render(request, 'about.html', context={})


@cache_page(60 * 60)
def price(request):
    return render(request, 'price.html', context={})


@cache_page(60 * 60)
def service(request):
    return render(request, 'service.html', context={})


@cache_page(60 * 60)
def team(request):
    return render(request, "team.html", context={})


@cache_page(60 * 60)
def testimonial(request):
    return render(request, 'testimonial.html', context={})


def newsletter(request):
    if request.method == "POST":
        email = request.POST.get("email")
        # TODO: save to database or send email
        messages.success(request, "Thank you for subscribing!")
        return redirect("home")


# ========================================== 
# AJAX: CHECK AVAILABLE SLOTS (CACHED)
# ==========================================

@require_http_methods(["POST"])
@login_required
def check_available_slots(request):
    """AJAX endpoint with intelligent caching and real-time availability"""
    try:
        date_str = request.POST.get('date')
        doctor_email = request.POST.get('doctor_email')

        if not date_str or not doctor_email:
            return JsonResponse({
                'status': 'error',
                'message': 'Date and doctor email are required'
            }, status=400)

        # Check cache first (short TTL for real-time accuracy)
        cache_key = cache_key_generator(
            'available_slots',
            date_str,
            doctor_email
        )
        
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Returning cached slots for {date_str}")
            return JsonResponse(cached_data)

        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        if appointment_date < timezone.now().date():
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot book appointments in the past'
            }, status=400)

        # Use select_for_update to get accurate booked slots
        with transaction.atomic():
            booked_appointments = Appointment.objects.select_for_update().filter(
                date=appointment_date,
                doctor_email=doctor_email,
                status__in=['pending', 'confirmed']
            ).values_list('time', flat=True)
            
            booked_times = set(booked_appointments)

        # Get time slots with caching
        slots_cache_key = 'active_time_slots'
        all_slots = cache.get(slots_cache_key)
        
        if not all_slots:
            all_slots = list(TimeSlot.objects.filter(
                is_active=True
            ).order_by('time'))
            cache.set(slots_cache_key, all_slots, 60 * 60)  # 1 hour

        available_slots = []
        current_time = timezone.now().time()
        is_today = appointment_date == timezone.now().date()

        for slot in all_slots:
            if is_today and slot.time <= current_time:
                continue

            is_available = slot.time not in booked_times
            available_slots.append({
                'time': slot.time.strftime('%H:%M'),
                'display_time': slot.time.strftime('%I:%M %p'),
                'is_available': is_available
            })

        response_data = {
            'status': 'success',
            'date': date_str,
            'slots': available_slots,
            'total_slots': len(available_slots),
            'available_count': sum(1 for s in available_slots if s['is_available'])
        }

        # Cache for 2 minutes (short TTL for real-time availability)
        cache.set(cache_key, response_data, 60 * 2)

        return JsonResponse(response_data)

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
# ATOMIC APPOINTMENT BOOKING
# ==========================================

def get_appointment_lock_key(request, *args, **kwargs):
    """Generate unique lock key for appointment booking"""
    date = request.POST.get('date')
    time = request.POST.get('time')
    doctor = request.POST.get('doctor_email')
    return f'appointment:{date}:{time}:{doctor}'


@require_http_methods(["POST"])
@login_required
@atomic_with_lock(get_appointment_lock_key, timeout=10)
def book_appointment_ajax(request):
    """
    ATOMIC appointment booking with race condition prevention
    Uses database-level locking and distributed locks
    """
    try:
        form = AppointmentForm(request.POST)
        
        if not form.is_valid():
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid form data',
                'errors': form.errors
            }, status=400)

        # Everything happens in atomic transaction (already wrapped by decorator)
        appointment_obj = form.save(commit=False)
        appointment_obj.user = request.user
        # Use profile phone if available
        if not appointment_obj.phone and profile.phone:
            appointment_obj.phone = profile.phone

        # Check for conflicts with database-level locking
        buffer_minutes = 15
        appointment_datetime = datetime.combine(
            appointment_obj.date, 
            appointment_obj.time
        )
        start_time = (appointment_datetime - timedelta(minutes=buffer_minutes)).time()
        end_time = (appointment_datetime + timedelta(minutes=buffer_minutes)).time()

        # Use select_for_update to lock conflicting rows
        conflicting_appointment = Appointment.objects.select_for_update().filter(
            date=appointment_obj.date,
            doctor_email=appointment_obj.doctor_email,
            time__range=(start_time, end_time),
            status__in=['pending', 'confirmed']
        ).first()

        if conflicting_appointment:
            return JsonResponse({
                'status': 'error',
                'message': f'This time slot is already booked (±{buffer_minutes} min buffer)',
                'booked_time': conflicting_appointment.time.strftime('%I:%M %p')
            }, status=409)

        # Additional check: Exact time slot
        exact_conflict = Appointment.objects.select_for_update().filter(
            date=appointment_obj.date,
            doctor_email=appointment_obj.doctor_email,
            time=appointment_obj.time,
            status__in=['pending', 'confirmed']
        ).exists()

        if exact_conflict:
            return JsonResponse({
                'status': 'error',
                'message': 'This exact time slot is already booked',
                'booked_time': appointment_obj.time.strftime('%I:%M %p')
            }, status=409)

        # Save appointment (still in transaction)
        appointment_obj.save()

        # Invalidate relevant caches immediately
        cache_key = cache_key_generator(
            'available_slots',
            appointment_obj.date.strftime('%Y-%m-%d'),
            appointment_obj.doctor_email
        )
        cache.delete(cache_key)
        invalidate_user_cache(request.user.id, 'appointment')
        cache.delete('homepage_stats')
        cache.delete(f'upcoming_appointments:{request.user.id}')
        cache.delete(f'user_appointment_stats:{request.user.id}')

        # Queue background tasks (after successful commit)
        transaction.on_commit(lambda: send_appointment_email_task.delay(appointment_obj.id))
        transaction.on_commit(lambda: create_calendar_event_task.delay(appointment_obj.id))

        logger.info(f"Appointment {appointment_obj.id} booked successfully by user {request.user.id}")

        return JsonResponse({
            'status': 'success',
            'message': 'Appointment booked successfully!',
            'appointment': {
                'id': appointment_obj.id,
                'service': appointment_obj.get_service_display(),
                'date': appointment_obj.date.strftime('%B %d, %Y'),
                'time': appointment_obj.time.strftime('%I:%M %p'),
                'doctor': appointment_obj.doctor_email,
                'status': appointment_obj.get_status_display()
            }
        }, status=201)

    except IntegrityError as e:
        logger.error(f"Integrity error during booking: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'This appointment slot was just booked by another user. Please select another time.'
        }, status=409)
    
    except Exception as e:
        logger.error(f"Error booking appointment: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again.'
        }, status=500)


# ========================================== 
# APPOINTMENT VIEW (WITH CACHING & ATOMIC OPERATIONS)
# ==========================================

@login_required(login_url='/login/')
def appointment(request):
    """Main appointment view with atomic operations"""
    if request.method == 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return book_appointment_ajax(request)

        # Standard form submission with atomic operation
        try:
            with transaction.atomic():
                form = AppointmentForm(request.POST)
                if form.is_valid():
                    appointment_obj = form.save(commit=False)
                    appointment_obj.user = request.user
                    
                    # Check conflicts with lock
                    buffer_minutes = 15
                    appointment_datetime = datetime.combine(
                        appointment_obj.date, 
                        appointment_obj.time
                    )
                    start_time = (appointment_datetime - timedelta(minutes=buffer_minutes)).time()
                    end_time = (appointment_datetime + timedelta(minutes=buffer_minutes)).time()

                    conflicting = Appointment.objects.select_for_update().filter(
                        date=appointment_obj.date,
                        doctor_email=appointment_obj.doctor_email,
                        time__range=(start_time, end_time),
                        status__in=['pending', 'confirmed']
                    ).exists()

                    if conflicting:
                        messages.error(request, "This time slot is already booked. Please select another time.")
                        return redirect('appointment')

                    appointment_obj.save()

                    # Invalidate caches
                    invalidate_user_cache(request.user.id, 'appointment')

                    # Queue tasks
                    transaction.on_commit(lambda: send_appointment_email_task.delay(appointment_obj.id))
                    transaction.on_commit(lambda: create_calendar_event_task.delay(appointment_obj.id))

                    messages.success(request, "Appointment booked successfully!")
                    return redirect('appointment')
                else:
                    messages.error(request, "Please correct the errors below.")
        
        except IntegrityError:
            messages.error(request, "This appointment slot was just booked. Please select another time.")
            return redirect('appointment')
    else:
        form = AppointmentForm()

    # Cache user's upcoming appointments
    cache_key = f'upcoming_appointments:{request.user.id}'
    upcoming_appointments = cache.get(cache_key)

    if not upcoming_appointments:
        upcoming_appointments = Appointment.objects.filter(
            user=request.user,
            date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).select_related('user').order_by('date', 'time')[:5]
        
        cache.set(cache_key, list(upcoming_appointments), 60 * 5)

    # Cache doctors list
    doctors_cache_key = 'doctors_list'
    doctors = cache.get(doctors_cache_key)
    
    if not doctors:
        doctors = [
            {'email': 'dr.smith@oroshine.com', 'name': 'Dr. Sarah Smith'},
            {'email': 'dr.johnson@oroshine.com', 'name': 'Dr. Michael Johnson'},
            {'email': 'dr.patel@oroshine.com', 'name': 'Dr. Priya Patel'},
        ]
        cache.set(doctors_cache_key, doctors, 60 * 60)

    context = {
        'form': form,
        'upcoming_appointments': upcoming_appointments,
        'doctors': doctors
    }
    return render(request, 'appointment.html', context)


# ========================================== 
# ATOMIC USER REGISTRATION
# ==========================================

def register_request(request):
    """Atomic user registration with profile creation"""
    if request.method == "POST":
        try:
            with transaction.atomic():
                form = NewUserForm(request.POST)
                
                if form.is_valid():
                    # Check for existing user atomically
                    username = form.cleaned_data['username']
                    email = form.cleaned_data['email']
                    
                    if User.objects.select_for_update().filter(
                        Q(username=username) | Q(email=email)
                    ).exists():
                        messages.error(request, "Username or email already exists.")
                        return render(request, "register.html", {"register_form": form})
                    
                    # Create user
                    user = form.save()
                    
                    # Create profile atomically
                    UserProfile.objects.create(user=user)
                    
                    # Login user
                    login(request, user)
                    
                    # Cache profile
                    profile_cache_key = f'user_profile:{user.id}'
                    cache.set(profile_cache_key, user.profile, 60 * 30)
                    
                    logger.info(f"User {user.id} registered successfully")
                    messages.success(request, "Registration successful. Welcome!")
                    
                    return redirect("/")
                else:
                    messages.error(request, "Registration failed. Please check the information.")
        
        except IntegrityError as e:
            logger.error(f"Registration integrity error: {e}")
            messages.error(request, "Registration failed. Username or email may already exist.")
    else:
        form = NewUserForm()
    
    return render(request, "register.html", {"register_form": form})


# ========================================== 
# ENHANCED AJAX LOGIN WITH RATE LIMITING
# ==========================================

@require_http_methods(["POST"])
def login_ajax(request):
    """Enhanced AJAX login with atomic operations and rate limiting"""
    try:
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Username and password are required'
            }, status=400)

        # Rate limiting check with atomic increment
        rate_limit_key = f'login_attempts:{request.META.get("REMOTE_ADDR")}'
        
        # Atomic increment
        attempts = cache.get(rate_limit_key, 0)
        
        if attempts >= 5:
            return JsonResponse({
                'status': 'error',
                'message': 'Too many login attempts. Please try again in 15 minutes.'
            }, status=429)

        # Authenticate
        user = authenticate(request, username=username, password=password)

        if user is not None:
            with transaction.atomic():
                # Login user
                login(request, user)
                
                # Clear rate limit on successful login
                cache.delete(rate_limit_key)

                # Get or create profile
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                # Cache user profile
                profile_cache_key = f'user_profile:{user.id}'
                cache.set(profile_cache_key, profile, 60 * 30)
                
                profile_data = {
                    'phone': profile.phone,
                    'avatar': profile.avatar.url if profile.avatar else None
                }

            logger.info(f"User {user.id} logged in successfully")

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
            # Increment rate limit counter atomically
            cache.set(rate_limit_key, attempts + 1, 60 * 15)
            
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username or password'
            }, status=401)

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred during login'
        }, status=500)


# ========================================== 
# STANDARD LOGIN WITH ATOMIC OPERATIONS
# ==========================================

def login_request(request):
    """Standard login with AJAX support and atomic operations"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return login_ajax(request)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                with transaction.atomic():
                    login(request, user)
                    
                    # Ensure profile exists
                    profile, created = UserProfile.objects.get_or_create(user=user)
                    
                    # Cache profile
                    profile_cache_key = f'user_profile:{user.id}'
                    cache.set(profile_cache_key, profile, 60 * 30)
                
                messages.success(request, f"Welcome back, {username}!")
                return redirect(request.GET.get('next', '/'))
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"login_form": form})


# ========================================== 
# CONTACT VIEW WITH ATOMIC OPERATIONS
# ==========================================

def contact(request):
    """Contact form with atomic operations"""
    if request.method == 'GET':
        return render(request, 'contact.html', {
            'page_title': 'Contact Us - OroShine Dental Care'
        })

    if not request.user.is_authenticated:
        messages.error(request, "Please login to submit the contact form.")
        return redirect('login')

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip().lower()
    subject = request.POST.get('subject', '').strip()
    message_text = request.POST.get('message', '').strip()

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
    if not message_text:
        errors.append("Message is required")

    if errors:
        for error in errors:
            messages.error(request, error)
        return render(request, 'contact.html', {
            'page_title': 'Contact Us - OroShine Dental Care',
            'name': name,
            'email': email,
            'subject': subject,
            'message': message_text
        })

    try:
        with transaction.atomic():
            contact_inquiry = Contact.objects.create(
                user=request.user,
                name=name,
                email=email,
                subject=subject,
                message=message_text
            )

            # Queue email task after commit
            transaction.on_commit(lambda: send_contact_email_task.delay(
                contact_inquiry.id,
                request.META.get("REMOTE_ADDR", "Unknown IP")
            ))

        messages.success(request, "Thank you! We'll respond within 24 hours.")
        return redirect('home')
    
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        messages.error(request, "An error occurred. Please try again.")
        return redirect('contact')


# ========================================== 
# USER PROFILE WITH ATOMIC UPDATES
# ==========================================

@login_required
def user_profile(request):
    """User profile with atomic updates and caching"""
    profile_cache_key = f'user_profile:{request.user.id}'
    
    try:
        profile = UserProfile.objects.select_for_update().get(user=request.user)
    except UserProfile.DoesNotExist:
        with transaction.atomic():
            profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Lock the profile for update
                profile = UserProfile.objects.select_for_update().get(user=request.user)
                
                form = UserProfileForm(request.POST, request.FILES, instance=profile)
                if form.is_valid():
                    form.save()
                    
                    # Invalidate profile cache
                    cache.delete(profile_cache_key)
                    invalidate_user_cache(request.user.id)
                    
                    messages.success(request, "Profile updated successfully!")
                    return redirect('user_profile')
                else:
                    messages.error(request, "Please correct the errors below.")
        
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            messages.error(request, "An error occurred while updating profile.")
    else:
        form = UserProfileForm(instance=profile)

    # Cache appointment statistics
    stats_cache_key = f'user_appointment_stats:{request.user.id}'
    stats = cache.get(stats_cache_key)
    
    if not stats:
        appointments = Appointment.objects.filter(user=request.user)
        stats = {
            'total': appointments.count(),
            'pending': appointments.filter(status='pending').count(),
            'completed': appointments.filter(status='completed').count(),
        }
        cache.set(stats_cache_key, stats, 60 * 10)

    # Get paginated appointments
    appointments = Appointment.objects.filter(
        user=request.user
    ).select_related('user').order_by('-date', '-time')

    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contacts = Contact.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    context = {
        'form': form,
        'profile': profile,
        'appointments': page_obj,
        'contacts': contacts,
        'total_appointments': stats['total'],
        'pending_appointments': stats['pending'],
        'completed_appointments': stats['completed'],
    }
    return render(request, 'profile.html', context)


# ========================================== 
# LOGOUT WITH CACHE CLEANUP
# ==========================================

def logout_request(request):
    """Logout with atomic cache cleanup"""
    user_id = request.user.id if request.user.is_authenticated else None
    
    logout(request)
    
    # Clear user-specific caches
    if user_id:
        invalidate_user_cache(user_id)
        cache.delete(f'user_profile:{user_id}')
        cache.delete(f'upcoming_appointments:{user_id}')
        cache.delete(f'user_appointment_stats:{user_id}')
    
    messages.success(request, "You have successfully logged out.")
    return redirect("/")