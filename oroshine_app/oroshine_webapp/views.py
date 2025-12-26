from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.validators import validate_email, ValidationError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
import logging
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from functools import wraps
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User
from django.utils.text import slugify
import re
import json
import random
from django.conf import settings
from django.http import HttpResponse


from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


from .models import (
    Contact, Appointment, UserProfile,
    DOCTOR_CHOICES, TIME_SLOTS, STATUS_CHOICES,SERVICE_CHOICES
)
from .forms import NewUserForm, UserProfileForm,AppointmentForm

from .tasks import (
    send_appointment_email_task,
    create_calendar_event_task
)



logger = logging.getLogger(__name__)






def prometheus_metrics(request):
    """Expose Prometheus metrics"""
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)

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
            
            cache_key = f"ratelimit:{key_prefix}:{identifier}"
            attempts = cache.get(cache_key, 0)
            
            if attempts >= limit:
                msg = f'Too many attempts. Please try again in {window // 60} minutes.'
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': msg}, status=429)
                else:
                    messages.error(request, msg)
                    return redirect('login')
            
            response = view_func(request, *args, **kwargs)
            
            # Only increment on failure (checks both JSON and Status Codes)
            is_failure = False
            if isinstance(response, JsonResponse):
                try:
                    data = json.loads(response.content.decode('utf-8'))
                    if data.get('status') == 'error': is_failure = True
                except: pass
            elif response.status_code >= 400:
                is_failure = True

            if is_failure:
                cache.set(cache_key, attempts + 1, window)
            # Optional: Reset on success to be user-friendly
            # else: cache.delete(cache_key) 
            
            return response
        return wrapper
    return decorator


# ==========================================
# HELPERS
# ==========================================

def invalidate_user_cache(user_id):
    keys = [
        f'user_profile:{user_id}',
        f'sidebar_appt:{user_id}',
        f'user_appointment_stats:{user_id}',
    ]
    for key in keys:
        cache.delete(key)

def is_valid_username(username):
    if not username or len(username) < 3 or len(username) > 150:
        return False, "Username must be between 3 and 150 characters"
    if not re.match(r'^[\w.@+-]+$', username):
        return False, "Username can only contain letters, numbers, and @/./+/-/_ characters"
    return True, ""

def is_valid_email(email):
    try:
        validate_email(email)
        return True, ""
    except ValidationError:
        return False, "Invalid email format"

def generate_username_suggestion(base_username):
    base = slugify(base_username) or "user"
    for i in range(1, 100):
        suggestion = f"{base}{i}"
        if not User.objects.filter(username__iexact=suggestion).exists():
            return suggestion
    return f"{base}{random.randint(100, 9999)}"


# ==========================================
# AUTH VIEWS
# ==========================================

@require_http_methods(["GET"])
@rate_limit('check_availability', limit=20, window=60)
def check_availability(request):
    username = request.GET.get('username', '').strip()
    email = request.GET.get('email', '').strip()
    
    if not username and not email:
        return JsonResponse({'status': 'error', 'message': 'Username or email required'}, status=400)
    
    cache_key = f"availability:{username or email}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse(cached_result)
    
    response_data = {}
    
    if username:
        is_valid, error_msg = is_valid_username(username)
        if not is_valid:
            response_data = {'status': 'error', 'is_taken': True, 'message': error_msg}
        else:
            is_taken = User.objects.filter(username__iexact=username).exists()
            response_data = {
                'status': 'success',
                'is_taken': is_taken,
                'message': f'Username "{username}" is already taken' if is_taken else 'Username available',
                'suggestion': generate_username_suggestion(username) if is_taken else ''
            }
    
    elif email:
        is_valid, error_msg = is_valid_email(email)
        if not is_valid:
            response_data = {'status': 'error', 'is_taken': True, 'message': error_msg}
        else:
            is_taken = User.objects.filter(email__iexact=email).exists()
            response_data = {
                'status': 'success',
                'is_taken': is_taken,
                'message': 'Email already registered' if is_taken else 'Email available'
            }
    
    cache.set(cache_key, response_data, 300)
    return JsonResponse(response_data)


@rate_limit('register', limit=5, window=3600)
def register_request(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    UserProfile.objects.create(user=user)
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, "Registration successful!")
                    return redirect('home')
            except IntegrityError:
                messages.error(request, "Username or email already exists.")
            except Exception as e:
                logger.error(f"Registration error: {e}")
                messages.error(request, "An unexpected error occurred.")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = NewUserForm()
    
    return render(request, "register.html", {"register_form": form})


@rate_limit('login', limit=5, window=900)
def login_request(request):
    if request.user.is_authenticated:
        return redirect('home')

    # Handle AJAX Login
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                return JsonResponse({'status': 'error', 'message': 'Account disabled.'}, status=403)
            login(request, user)
            UserProfile.objects.get_or_create(user=user)
            return JsonResponse({'status': 'success', 'redirect_url': request.GET.get('next', '/')})
        return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=401)

    # Handle Standard Login
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            UserProfile.objects.get_or_create(user=user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(request.GET.get('next', '/'))
        else:
            messages.error(request, "Invalid credentials.")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"login_form": form})


def logout_request(request):
    user_id = request.user.id if request.user.is_authenticated else None
    logout(request)
    if user_id:
        invalidate_user_cache(user_id)
    messages.success(request, "Logged out successfully.")
    return redirect("/")


# ==========================================
# PUBLIC PAGES (CACHED)
# ==========================================

def homepage(request):
    stats = cache.get('homepage_stats')
    if not stats:
        stats = {
            'total_appointments': Appointment.objects.filter(status='completed').count(),
            'active_users': UserProfile.objects.filter(user__is_active=True).count(),
            'satisfaction_rate': 98
        }
        cache.set('homepage_stats', stats, 1800)
    return render(request, 'index.html', {'stats': stats})

@cache_page(3600)
def about(request): return render(request, 'about.html')

@cache_page(3600)
def price(request): return render(request, 'price.html')

@cache_page(3600)
def service(request): return render(request, 'service.html')

@cache_page(3600)
def team(request): return render(request, "team.html")

@cache_page(3600)
def testimonial(request): return render(request, 'testimonial.html')


# ==========================================
# APPOINTMENT LOGIC + ajax slot check 
# ==========================================

# @require_http_methods(["POST"])
# @login_required
# def check_slots_ajax(request):
#     doctor = request.POST.get('doctor_email')
#     date = request.POST.get('date')

#     if not doctor or not date:
#         return JsonResponse({'status': 'error'}, status=400)

#     cache_key = f"slots:{doctor}:{date}"
#     booked = cache.get(cache_key)

#     if booked is None:
#         booked = set(
#             Appointment.objects.filter(
#                 doctor_email=doctor,
#                 date=date,
#                 status__in=['pending', 'confirmed']
#             ).values_list('time', flat=True)
#         )
#         cache.set(cache_key, booked, 300)

#     slots = [
#         {
#             "time": t,
#             "display": d,
#             "is_available": t not in booked
#         }
#         for t, d in TIME_SLOTS
#     ]

#     return JsonResponse({'status': 'success', 'slots': slots})


# @login_required(login_url='/login/')
# def appointment(request):
#     if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
#         form = AppointmentForm(request.POST)
#         if not form.is_valid():
#             return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

#         data = form.cleaned_data

#         try:
#             with transaction.atomic():
#                 exists = Appointment.objects.select_for_update().filter(
#                     date=data['date'],
#                     time=data['time'],
#                     doctor_email=data['doctor_email'],
#                     status__in=['pending', 'confirmed']
#                 ).exists()

#                 if exists:
#                     return JsonResponse(
#                         {'status': 'error', 'message': 'Slot already booked'},
#                         status=409
#                     )

#                 appt = Appointment.objects.create(
#                     user=request.user,
#                     **data,
#                     status='pending'
#                 )

#                 # invalidate slot cache
#                 cache.delete(f"slots:{data['doctor_email']}:{data['date']}")

#                 transaction.on_commit(lambda: send_appointment_email_task.delay(appt.id))
#                 transaction.on_commit(lambda: create_calendar_event_task.delay(appt.id))

#             return JsonResponse({
#                 'status': 'success',
#                 'message': 'Appointment booked successfully!',
#                 'redirect_url': '/appointment/'
#             })

#         except Exception:
#             return JsonResponse({'status': 'error', 'message': 'Server error'}, status=500)

#     # -------------------------------
#     # GET PAGE (NO DB HIT)
#     # -------------------------------
#     form = AppointmentForm()
#     return render(request, 'appointment.html', {
#         'form': form,
#         'doctor_choices': DOCTOR_CHOICES,
#     })



# v2 









# ==========================================
# AJAX SLOT AVAILABILITY CHECK
# ==========================================
@require_http_methods(["POST"])
@login_required
def check_slots_ajax(request):
    """
    Check available appointment slots for a doctor on a specific date
    Returns: JSON with slot availability
    """
    doctor = request.POST.get('doctor_email', '').strip()
    date = request.POST.get('date', '').strip()

    # Validation
    if not doctor or not date:
        return JsonResponse({
            'status': 'error',
            'message': 'Doctor and date are required'
        }, status=400)

    try:
        # Generate cache key
        cache_key = f"slots:{doctor}:{date}"
        
        # Try to get from cache
        booked = cache.get(cache_key)

        if booked is None:
            # Query database for booked slots
            booked = set(
                Appointment.objects.filter(
                    doctor_email=doctor,
                    date=date,
                    status__in=['pending', 'confirmed']
                ).values_list('time', flat=True)
            )
            
            # Cache for 5 minutes
            cache.set(cache_key, booked, 300)
            logger.debug(f"Cache miss for slots: {cache_key}")
        else:
            logger.debug(f"Cache hit for slots: {cache_key}")

        # Build slot list with availability
        slots = [
            {
                "time": str(time_obj),
                "display": display,
                "is_available": time_obj not in booked
            }
            for time_obj, display in TIME_SLOTS
        ]

        return JsonResponse({
            'status': 'success',
            'slots': slots,
            'doctor': doctor,
            'date': date
        })

    except Exception as e:
        logger.exception(f"Error checking slots for {doctor} on {date}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to check slot availability'
        }, status=500)


# ==========================================
# APPOINTMENT BOOKING VIEW
# ==========================================
@login_required(login_url='/custom-login/')
def appointment(request):
    """
    Handle appointment booking (GET: show form, POST: process booking)
    """
    
    # -------------------------------
    # AJAX POST: Book Appointment
    # -------------------------------
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        form = AppointmentForm(request.POST)
        
        if not form.is_valid():
            errors = form.errors.as_json()
            logger.warning(f"Invalid appointment form: {errors}")
            return JsonResponse({
                'status': 'error',
                'message': 'Please check your input and try again',
                'errors': form.errors
            }, status=400)

        data = form.cleaned_data

        try:
            with transaction.atomic():
                # Lock the row to prevent race conditions
                exists = Appointment.objects.select_for_update().filter(
                    date=data['date'],
                    time=data['time'],
                    doctor_email=data['doctor_email'],
                    status__in=['pending', 'confirmed']
                ).exists()

                if exists:
                    logger.info(
                        f"Slot conflict for user {request.user.id}: "
                        f"{data['doctor_email']} at {data['date']} {data['time']}"
                    )
                    print(request.user.id )
                    return JsonResponse({
                        'status': 'error',
                        'message': 'This time slot has already been booked. Please choose another.'
                    }, status=409)

                # Create appointment
                appt = Appointment.objects.create(
                    user=request.user,
                    name=data['name'],
                    email=data['email'],
                    phone=data.get('phone', ''),
                    date=data['date'],
                    time=data['time'],
                    doctor_email=data['doctor_email'],
                    service=data['service'],
                    message=data.get('message', ''),
                    status='pending'
                )

                logger.info(f"Appointment created: ID={appt.id}, User={request.user.id}")
                print(appt.id)
                print(appt)

                # Invalidate slot cache immediately
                cache_key = f"slots:{data['doctor_email']}:{data['date']}"
                cache.delete(cache_key)
                logger.debug(f"Invalidated cache: {cache_key}")

                # Queue async tasks AFTER transaction commits
                def queue_tasks():
                    try:
                        # Send confirmation email
                        email_result = send_appointment_email_task.apply_async(
                            args=[appt.id],
                            countdown=2,  # Small delay to ensure DB commit
                            retry=True
                        )
                        logger.info(f"Email task queued: {email_result.id}")
                        
                        # Create calendar event
                        calendar_result = create_calendar_event_task.apply_async(
                            args=[appt.id],
                            countdown=2,  # Slightly longer delay
                            retry=True
                        )
                        logger.info(f"Calendar task queued: {calendar_result.id}")
                        print(calendar_result)
                        print(email_result)
                    except Exception as e:
                        logger.exception(f"Error queuing tasks for appointment {appt.id}")

                transaction.on_commit(queue_tasks)

            return JsonResponse({
                'status': 'success',
                'message': 'Appointment booked successfully! Confirmation email will be sent shortly.',
                'appointment_id': appt.id,
                'redirect_url': '/appointment'  # Redirect to user's appointments
            })

        except Exception as e:
            logger.exception(f"Error booking appointment for user {request.user.id}")
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while booking your appointment. Please try again.'
            }, status=500)

    # -------------------------------
    # GET: Display Appointment Form
    # -------------------------------
    form = AppointmentForm(initial={
        'name': request.user.get_full_name(),
        'email': request.user.email
    })
    
    context = {
        'form': form,
        'doctor_choices': DOCTOR_CHOICES,
        'time_slots': TIME_SLOTS,
    }
    
    return render(request, 'appointment.html', context)




# ==========================================
# OPTIONAL: Cancel Appointment
# ==========================================
@require_http_methods(["POST"])
@login_required
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    try:
        appt = Appointment.objects.get(id=appointment_id, user=request.user)
        
        if appt.status in ['cancelled', 'completed']:
            return JsonResponse({
                'status': 'error',
                'message': f'Cannot cancel {appt.status} appointment'
            }, status=400)
        
        appt.status = 'cancelled'
        appt.save(update_fields=['status', 'updated_at'])
        
        # Invalidate cache
        cache_key = f"slots:{appt.doctor_email}:{appt.date}"
        cache.delete(cache_key)
        
        logger.info(f"Appointment {appointment_id} cancelled by user {request.user.id}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Appointment cancelled successfully'
        })
        
    except Appointment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Appointment not found'
        }, status=404)
    except Exception as e:
        logger.exception(f"Error cancelling appointment {appointment_id}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to cancel appointment'
        }, status=500)









# ==========================================
# PROFILE & CONTACT
# ==========================================

def contact(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Please login to submit.")
            return redirect('login')
            
        try:
            Contact.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                email=request.POST.get('email'),
                subject=request.POST.get('subject'),
                message=request.POST.get('message')
            )
            messages.success(request, "Message sent!")
            return redirect('home')
        except Exception:
            messages.error(request, "Error sending message.")
            
    return render(request, 'contact.html')


@login_required
def user_profile(request):
    user = request.user
    profile_key = f'user_profile:{user.id}'
    stats_key = f'user_appointment_stats:{user.id}'

    # Fetch Profile
    profile = cache.get(profile_key)
    if not profile:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        cache.set(profile_key, profile, 600)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            invalidate_user_cache(user.id) # Helper function
            messages.success(request, "Profile updated!")
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=profile)

    # Stats
    stats = cache.get(stats_key)
    if not stats:
        stats = Appointment.objects.with_counts_by_status(user.id)
        cache.set(stats_key, stats, 600)

    # Lists
    appointments = Appointment.objects.filter(user=user).select_related('user').order_by('-date')
    paginator = Paginator(appointments, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    contacts = Contact.objects.recent_for_user(user.id)

    context = {
        "form": form, "profile": profile, "appointments": page_obj, "contacts": contacts,
        "total_appointments": stats.get('total', 0),
        "pending_appointments": stats.get('pending', 0),
        "completed_appointments": stats.get('completed', 0),
    }
    return render(request, "profile.html", context)