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

from django.utils.text import slugify


from .models import Contact, Appointment, UserProfile, TimeSlot

from .tasks import (
    send_contact_email_task,
    send_appointment_email_task,
    create_calendar_event_task,
    # trigger_nocode_calendar_event
)

from .forms import NewUserForm, AppointmentForm, UserProfileForm

import re

logger = logging.getLogger(__name__)

# ========================================== 
# RATE LIMITING DECORATOR
# ==========================================

def rate_limit(key_prefix, limit=5, window=900):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            identifier = request.META.get('REMOTE_ADDR', 'unknown')
            if request.user.is_authenticated:
                identifier = f"user_{request.user.id}"
            
            cache_key = f"{key_prefix}:{identifier}"
            attempts = cache.get(cache_key, 0)
            
            if attempts >= limit:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Too many attempts. Please try again in {window // 60} minutes.'
                    }, status=429)
                else:
                    messages.error(request, f'Too many attempts. Please try again in {window // 60} minutes.')
                    return redirect('login')
            
            # Execute view FIRST
            response = view_func(request, *args, **kwargs)
            
            # FIXED: Only increment on actual failures
            if isinstance(response, JsonResponse):
                try:
                    data = json.loads(response.content.decode('utf-8'))
                    # Only increment if status is 'error' OR status code >= 400
                    if data.get('status') == 'error' or response.status_code >= 400:
                        cache.set(cache_key, attempts + 1, window)
                    elif data.get('status') == 'success':
                        # CLEAR on success
                        cache.delete(cache_key)
                except:
                    pass
            elif response.status_code >= 400:
                cache.set(cache_key, attempts + 1, window)
            
            return response
        return wrapper
    return decorator

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
# USERNAME/EMAIL VALIDATION UTILITIES
# ==========================================

def is_valid_username(username):
    """Validate username format"""
    if not username or len(username) < 3 or len(username) > 150:
        return False, "Username must be between 3 and 150 characters"
    
    if not re.match(r'^[\w.@+-]+$', username):
        return False, "Username can only contain letters, numbers, and @/./+/-/_ characters"
    
    return True, ""


def is_valid_email(email):
    """Validate email format"""
    try:
        validate_email(email)
        return True, ""
    except ValidationError:
        return False, "Invalid email format"


def generate_username_suggestion(base_username):
    """Generate unique username suggestion"""
    base = slugify(base_username) or "user"
    
    # Try with numbers
    for i in range(1, 100):
        suggestion = f"{base}{i}"
        if not User.objects.filter(username__iexact=suggestion).exists():
            return suggestion
    
    # Fallback with random number
    return f"{base}{random.randint(100, 9999)}"


# ========================================== 
# AJAX: CHECK USERNAME/EMAIL AVAILABILITY
# ==========================================

@require_http_methods(["GET"])
@rate_limit('check_availability', limit=20, window=60)
def check_availability(request):
    """
    AJAX endpoint to check username/email availability with caching
    """
    username = request.GET.get('username', '').strip()
    email = request.GET.get('email', '').strip()
    
    if not username and not email:
        return JsonResponse({
            'status': 'error',
            'message': 'Username or email is required'
        }, status=400)
    
    # Create cache key
    cache_key = f"availability_check:{username or email}"
    cached_result = cache.get(cache_key)
    
    if cached_result is not None:
        return JsonResponse(cached_result)
    
    response_data = {'is_taken': False, 'suggestion': '', 'message': ''}
    
    if username:
        # Validate username format
        is_valid, error_msg = is_valid_username(username)
        if not is_valid:
            response_data = {
                'status': 'error',
                'is_taken': True,
                'message': error_msg,
                'suggestion': ''
            }
        else:
            # Check availability
            is_taken = User.objects.filter(username__iexact=username).exists()
            response_data = {
                'status': 'success',
                'is_taken': is_taken,
                'message': f'Username "{username}" is already taken' if is_taken else 'Username is available',
                'suggestion': generate_username_suggestion(username) if is_taken else ''
            }
    
    elif email:
        # Validate email format
        is_valid, error_msg = is_valid_email(email)
        if not is_valid:
            response_data = {
                'status': 'error',
                'is_taken': True,
                'message': error_msg,
                'suggestion': ''
            }
        else:
            # Check availability
            is_taken = User.objects.filter(email__iexact=email).exists()
            response_data = {
                'status': 'success',
                'is_taken': is_taken,
                'message': 'Email is already registered' if is_taken else 'Email is available',
                'suggestion': ''
            }
    
    # Cache result for 5 minutes
    cache.set(cache_key, response_data, 300)
    
    return JsonResponse(response_data)


# ========================================== 
# ATOMIC USER REGISTRATION
# ==========================================

@rate_limit('register', limit=5, window=3600)
def register_request(request):
    """Atomic user registration with profile creation and proper validation"""
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('home')
    
    if request.method == "POST":
        try:
            with transaction.atomic():
                form = NewUserForm(request.POST)
                
                if form.is_valid():
                    username = form.cleaned_data['username']
                    email = form.cleaned_data['email'].lower()
                    
                    # Double-check availability with select_for_update
                    existing_user = User.objects.select_for_update().filter(
                        Q(username__iexact=username) | Q(email__iexact=email)
                    ).first()
                    
                    if existing_user:
                        if existing_user.username.lower() == username.lower():
                            form.add_error('username', 'This username is already taken.')
                        if existing_user.email.lower() == email:
                            form.add_error('email', 'This email is already registered.')
                        
                        messages.error(request, "Username or email already exists.")
                        return render(request, "register.html", {"register_form": form})
                    
                    # Create user
                    user = form.save(commit=False)
                    user.email = email
                    user.save()
                    
                    # Create profile atomically
                    profile, created = UserProfile.objects.get_or_create(user=user)
                    
                    # Clear availability cache
                    cache.delete(f"availability_check:{username}")
                    cache.delete(f"availability_check:{email}")
                    
                    # Login user
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    
                    # Cache profile
                    profile_cache_key = f'user_profile:{user.id}'
                    cache.set(profile_cache_key, profile, 1800)
                    
                    # Clear rate limit on successful registration
                    identifier = request.META.get('REMOTE_ADDR', 'unknown')
                    cache.delete(f"register:{identifier}")
                    
                    logger.info(f"User {user.id} ({username}) registered successfully")
                    messages.success(request, "Registration successful! Welcome to OroShine Dental Care.")
                    
                    return redirect('home')
                else:
                    # Form validation errors
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field.title()}: {error}")
        
        except IntegrityError as e:
            logger.error(f"Registration integrity error: {e}")
            messages.error(request, "Registration failed. Username or email may already exist.")
        
        except Exception as e:
            logger.error(f"Registration error: {e}", exc_info=True)
            messages.error(request, "An unexpected error occurred. Please try again.")
    
    else:
        form = NewUserForm()
    
    return render(request, "register.html", {"register_form": form})


# ========================================== 
# AJAX LOGIN WITH RATE LIMITING
# ==========================================
@require_http_methods(["POST"])
@rate_limit('login_ajax', limit=5, window=900)
def login_ajax(request):
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
            if not user.is_active:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Your account has been disabled.'
                }, status=403)
            
            with transaction.atomic():
                login(request, user,backend='django.contrib.auth.backends.ModelBackend')
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile_cache_key = f'user_profile:{user.id}'
                cache.set(profile_cache_key, profile, 1800)
            
            # IMPORTANT: Clear rate limit on success
            identifier = request.META.get('REMOTE_ADDR', 'unknown')
            cache.delete(f"login_ajax:{identifier}")
            cache.delete(f"login:{identifier}")
            cache.delete(f"login_ajax:user_{user.id}")
            
            logger.info(f"User {user.id} logged in via AJAX")

            return JsonResponse({
                'status': 'success',
                'message': f'Welcome back, {user.first_name or user.username}!',
                'redirect_url': request.GET.get('next', '/')
            })
        else:
            # Return error without incrementing (decorator handles it)
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username or password'
            }, status=401)

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred during login.'
        }, status=500)
        
# ========================================== 
# STANDARD LOGIN WITH RATE LIMITING
# ==========================================

@rate_limit('login', limit=5, window=900)
def login_request(request):
    """Standard login with AJAX support and atomic operations"""
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('home')
    
    # Handle AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return login_ajax(request)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            
            if user is not None:
                if not user.is_active:
                    messages.error(request, "Your account has been disabled. Please contact support.")
                    return render(request, "login.html", {"login_form": form})
                
                with transaction.atomic():
                    login(request, user,backend='django.contrib.auth.backends.ModelBackend')
                    
                    # Ensure profile exists
                    profile, created = UserProfile.objects.get_or_create(user=user)
                    
                    # Cache profile
                    profile_cache_key = f'user_profile:{user.id}'
                    cache.set(profile_cache_key, profile, 1800)
                
                # Clear rate limit on successful login
                identifier = request.META.get('REMOTE_ADDR', 'unknown')
                cache.delete(f"login:{identifier}")
                
                logger.info(f"User {user.id} ({username}) logged in successfully")
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
# LOGOUT WITH CACHE CLEANUP
# ==========================================

def logout_request(request):
    """Logout with atomic cache cleanup"""
    user_id = request.user.id if request.user.is_authenticated else None
    username = request.user.username if request.user.is_authenticated else None
    
    logout(request)
    
    # Clear user-specific caches
    if user_id:
        invalidate_user_cache(user_id)
        cache.delete(f'user_profile:{user_id}')
        cache.delete(f'upcoming_appointments:{user_id}')
        cache.delete(f'user_appointment_stats:{user_id}')

    cache.clear()
    
    logger.info(f"User {user_id} ({username}) logged out successfully")
    messages.success(request, "You have successfully logged out.")
    return redirect("/")


# ========================================== 
# BASIC PAGES WITH CACHING
# ==========================================

# @cache_page(60 * 15)
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
            'satisfaction_rate': 98
        }
        cache.set('homepage_stats', stats, 1800)
    
    return render(request, 'index.html', {'stats': stats})


@cache_page(60 * 60)
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




# ==============================================
# appointments  and related view 
# =========



# ========================================== 
# CACHE & UTILS
# ==========================================

def invalidate_user_cache(user_id):
    """Clear specific user caches after an update"""
    cache.delete(f"sidebar_appt:{user_id}")
    cache.delete(f"user_stats:{user_id}")

# ========================================== 
# AJAX: CHECK AVAILABLE SLOTS (OPTIMIZED)
# ==========================================

@require_http_methods(["POST"])
@login_required
def check_available_slots(request):
    """
    Super-fast availability check.
    Comparies hardcoded TIME_SLOTS vs Database.
    """
    try:
        date_str = request.POST.get('date')
        doctor_id = request.POST.get('doctor_id') # Changed from email to ID

        if not date_str or not doctor_id:
            return JsonResponse({
                'status': 'error', 
                'message': 'Date and doctor are required'
            }, status=400)

        # 1. Check Cache (Fastest)
        cache_key = f"slots:{date_str}:{doctor_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse(cached_data)

        # 2. Validation
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if check_date < timezone.now().date():
            return JsonResponse({'status': 'error', 'message': 'Cannot book past dates'}, status=400)

        # 3. Query DB for TAKEN slots only (Single optimized query)
        # We only need the 'time' strings of confirmed bookings
        booked_times = set(Appointment.objects.filter(
            date=check_date,
            doctor_id=doctor_id,
            status__in=['pending', 'confirmed']
        ).values_list('time', flat=True))

        # 4. Compute Available Slots in Memory (Python is fast here)
        available_slots = []
        now = timezone.now()
        is_today = check_date == now.date()
        current_time_str = now.strftime('%H:%M')

        # Iterate through the hardcoded TIME_SLOTS tuple
        for time_val, time_label in TIME_SLOTS:
            # Skip past times if today
            if is_today and time_val <= current_time_str:
                continue

            is_available = time_val not in booked_times
            
            available_slots.append({
                'time': time_val,      # Value to send to DB (e.g., "09:00")
                'display': time_label, # Value to show User (e.g., "09:00 AM")
                'is_available': is_available
            })

        response_data = {
            'status': 'success',
            'date': date_str,
            'slots': available_slots,
            'available_count': sum(1 for s in available_slots if s['is_available'])
        }

        # 5. Cache result for 2 minutes
        cache.set(cache_key, response_data, 120)

        return JsonResponse(response_data)

    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid date format'}, status=400)
    except Exception as e:
        logger.error(f"Slot check error: {e}")
        return JsonResponse({'status': 'error', 'message': 'Server error'}, status=500)


# ========================================== 
# ATOMIC APPOINTMENT BOOKING (AJAX)
# ==========================================

@require_http_methods(["POST"])
@login_required
def book_appointment_ajax(request):
    """
    Handles the actual booking via AJAX.
    Uses Atomic Transactions and Celery.
    """
    try:
        # Use the optimized form (No DB queries on init)
        form = AppointmentForm(request.POST)
        
        if not form.is_valid():
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid form data',
                'errors': form.errors
            }, status=400)

        # 1. ATOMIC WRITE
        with transaction.atomic():
            # Don't save to DB yet (commit=False)
            appt = form.save(commit=False)
            
            # Auto-fill User Data
            appt.user = request.user
            
            # MANUAL ID ASSIGNMENT (Critical Optimization)
            # We skip querying the Doctor/Service tables. We trust the IDs.
            appt.doctor_id = form.cleaned_data['doctor_id']
            appt.service_id = form.cleaned_data['service_id']
            
            # Fetch phone from profile if missing
            if not appt.phone and hasattr(request.user, 'profile'):
                appt.phone = request.user.profile.phone

            # SAVE (This is where the DB checks constraints)
            appt.save()

            # 2. TRIGGER BACKGROUND TASKS (Celery)
            # on_commit ensures tasks run only AFTER the DB transaction succeeds
            transaction.on_commit(lambda: send_appointment_email_task.delay(appt.id))
            transaction.on_commit(lambda: trigger_nocode_calendar_event.delay(appt.id))

            # 3. INVALIDATE CACHES
            invalidate_user_cache(request.user.id)
            # Clear slot cache for this doctor/date so others see it as booked
            cache.delete(f"slots:{appt.date}:{appt.doctor_id}")

            logger.info(f"Booking success: ID {appt.id} for {request.user}")

            return JsonResponse({
                'status': 'success',
                'message': 'Appointment confirmed! Sending email...',
                'redirect_url': '/appointment/' # Optional
            }, status=201)

    except IntegrityError:
        # This catches "Unique Constraint" (Double Booking) instantly
        return JsonResponse({
            'status': 'error',
            'message': 'This time slot was just taken by another patient. Please choose another.'
        }, status=409)
    
    except Exception as e:
        logger.error(f"Booking Error: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'System error. Please try again.'
        }, status=500)


# ========================================== 
# APPOINTMENT PAGE VIEW
# ==========================================

@login_required(login_url='/login/')
def appointment(request):
    """
    Renders the page. 
    If POST (Standard Submit), it reuses the logic above via function call 
    or handles it similarly (Preferred: use AJAX for everything).
    """
    
    # 1. Handle AJAX requests via the dedicated function
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return book_appointment_ajax(request)

    # 2. Standard POST (Fallback)
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    appt = form.save(commit=False)
                    appt.user = request.user
                    appt.doctor_id = form.cleaned_data['doctor_id']
                    appt.service_id = form.cleaned_data['service_id']
                    
                    if not appt.phone and hasattr(request.user, 'profile'):
                        appt.phone = request.user.profile.phone
                    
                    appt.save()
                    
                    # Tasks
                    transaction.on_commit(lambda: send_appointment_email_task.delay(appt.id))
                    transaction.on_commit(lambda: trigger_nocode_calendar_event.delay(appt.id))
                    
                    # Cache Cleanup
                    invalidate_user_cache(request.user.id)
                    cache.delete(f"slots:{appt.date}:{appt.doctor_id}")
                    
                    messages.success(request, "Appointment Booked Successfully!")
                    return redirect('appointment')

            except IntegrityError:
                messages.error(request, "Slot already booked. Please try another.")
            except Exception:
                messages.error(request, "Something went wrong.")
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        form = AppointmentForm()

    # 3. GET Request: Load Sidebar (Cached)
    sidebar_key = f"sidebar_appt:{request.user.id}"
    upcoming_appointments = cache.get(sidebar_key)
    
    if upcoming_appointments is None:
        # OPTIMIZATION: select_related fetches Doctor & Service in 1 query
        upcoming_appointments = Appointment.objects.filter(
            user=request.user,
            status__in=['pending', 'confirmed']
        ).select_related('doctor', 'service').order_by('date', 'time')[:5]
        
        cache.set(sidebar_key, upcoming_appointments, 300)

    context = {
        'form': form,
        'upcoming_appointments': upcoming_appointments,
    }
    return render(request, 'appointment.html', context)
















# ========================================== 
# CONTACT VIEW
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
# USER PROFILE
# ==========================================

@login_required
def user_profile(request):
    user = request.user
    profile_cache_key = f'user_profile:{user.id}'
    stats_cache_key = f'user_appointment_stats:{user.id}'

    # -----------------------------
    # 1) FETCH PROFILE (cached)
    # -----------------------------
    profile = cache.get(profile_cache_key)

    if not profile:
        # Ensure atomic creation/fetch
        with transaction.atomic():
            profile, created = UserProfile.objects.select_for_update().get_or_create(user=user)
        cache.set(profile_cache_key, profile, 600)

    # -----------------------------
    # 2) HANDLE POST (Update Profile)
    # -----------------------------
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Fetch fresh row locked for update
                profile = UserProfile.objects.select_for_update().get(user=user)
                form = UserProfileForm(request.POST, request.FILES, instance=profile)

                if form.is_valid():
                    form.save()

                    # Invalidate caches
                    cache.delete(profile_cache_key)
                    cache.delete(stats_cache_key)

                    messages.success(request, "Profile updated successfully!")
                    return redirect('user_profile')
                else:
                    messages.error(request, "Please correct the errors below.")
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            messages.error(request, "Something went wrong while updating your profile.")

    else:
        form = UserProfileForm(instance=profile)

    # -----------------------------
    # 3) APPOINTMENT STATS (cached)
    # -----------------------------
    stats = cache.get(stats_cache_key)
    if not stats:
        appointments = Appointment.objects.filter(user=user)
        stats = {
            "total": appointments.count(),
            "pending": appointments.filter(status="pending").count(),
            "completed": appointments.filter(status="completed").count(),
        }
        cache.set(stats_cache_key, stats, 600)

    # -----------------------------
    # 4) APPOINTMENT LIST (pagination)
    # -----------------------------
    appointment_list = (
        Appointment.objects.filter(user=user)
        .select_related("user")
        .order_by("-date", "-time")
    )

    paginator = Paginator(appointment_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # -----------------------------
    # 5) CONTACTS (small data)
    # -----------------------------
    contacts = Contact.objects.filter(user=user).order_by("-created_at")[:5]

    # -----------------------------
    # 6) RENDER TEMPLATE
    # -----------------------------
    context = {
        "form": form,
        "profile": profile,
        "appointments": page_obj,
        "contacts": contacts,
        "total_appointments": stats["total"],
        "pending_appointments": stats["pending"],
        "completed_appointments": stats["completed"],
    }

    return render(request, "profile.html", context)
