from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from PIL import Image
from django.utils import timezone

# for prometheous

from django.db.models.signals import post_save
from django.dispatch import receiver
from prometheus_client import Gauge

# ====================================
# CHOICES
# ====================================

DOCTOR_CHOICES = (
    ('nikhilchandurkar24@gmail.com', 'Dr. Worst Developer'),
    ('doctor.johnson@example.com', 'Dr. Johnson'),
    ('doctor.williams@example.com', 'Dr. Williams'),
    ('doctor.brown@example.com', 'Dr. Brown'),
)

TIME_SLOTS = (
    # Morning Slots: 09:00 AM – 02:00 PM
    ('09:00', '09:00 AM'), ('09:15', '09:15 AM'), ('09:30', '09:30 AM'), ('09:45', '09:45 AM'),
    ('10:00', '10:00 AM'), ('10:15', '10:15 AM'), ('10:30', '10:30 AM'), ('10:45', '10:45 AM'),
    ('11:00', '11:00 AM'), ('11:15', '11:15 AM'), ('11:30', '11:30 AM'), ('11:45', '11:45 AM'),
    ('12:00', '12:00 PM'), ('12:15', '12:15 PM'), ('12:30', '12:30 PM'), ('12:45', '12:45 PM'),
    ('13:00', '01:00 PM'), ('13:15', '01:15 PM'), ('13:30', '01:30 PM'), ('13:45', '01:45 PM'),
    ('14:00', '02:00 PM'),

    # Evening Slots: 06:00 PM – 09:00 PM
    ('18:00', '06:00 PM'), ('18:15', '06:15 PM'), ('18:30', '06:30 PM'), ('18:45', '06:45 PM'),
    ('19:00', '07:00 PM'), ('19:15', '07:15 PM'), ('19:30', '07:30 PM'), ('19:45', '07:45 PM'),
    ('20:00', '08:00 PM'), ('20:15', '08:15 PM'), ('20:30', '08:30 PM'), ('20:45', '08:45 PM'),
    ('21:00', '09:00 PM'),
)

STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
)

SERVICE_CHOICES = (
    ('checkup', 'General Checkup'),
    ('cleaning', 'Teeth Cleaning'),
    ('filling', 'Dental Filling'),
    ('extraction', 'Tooth Extraction'),
    ('root_canal', 'Root Canal'),
    ('whitening', 'Teeth Whitening'),
    ('braces', 'Braces Consultation'),
    ('emergency', 'Emergency'),
)



active_appointments = Gauge(
    'active_appointments_by_status',
    'Active appointments by status',
    ['status']
)



# ====================================
# CUSTOM MANAGERS
# ====================================

class UserProfileManager(models.Manager):
    def get_profile_with_user(self, user_id):
        return self.select_related('user').get(user_id=user_id)
    
    def active_profiles(self):
        return self.select_related('user').filter(user__is_active=True)


class AppointmentManager(models.Manager):
    def upcoming_for_user(self, user_id, limit=5):
        return (
            self.filter(
                user_id=user_id,
                status__in=['pending', 'confirmed'],
                date__gte=timezone.now().date()
            )
            .only('id', 'date', 'time', 'service', 'doctor_email', 'status')
            .order_by('date', 'time')[:limit]
        )
    
    def booked_slots(self, date, doctor_email):
        return set(
            self.filter(
                date=date,
                doctor_email=doctor_email,
                status__in=['pending', 'confirmed']
            ).values_list('time', flat=True)
        )
    
    def with_counts_by_status(self, user_id):
        from django.db.models import Count, Q
        return self.filter(user_id=user_id).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            confirmed=Count('id', filter=Q(status='confirmed')),
            completed=Count('id', filter=Q(status='completed')),
            cancelled=Count('id', filter=Q(status='cancelled'))
        )


class ContactManager(models.Manager):
    def recent_for_user(self, user_id, limit=5):
        return (
            self.filter(user_id=user_id)
            .only('id', 'subject', 'created_at', 'is_resolved')
            .order_by('-created_at')[:limit]
        )

# ====================================
# MODELS
# ====================================

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True, db_index=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    medical_history = models.TextField(max_length=1000, blank=True)
    allergies = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserProfileManager()

    class Meta:
        indexes = [
            models.Index(fields=['user', 'phone']),
            models.Index(fields=['city', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Profile #{self.user_id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Invalidate user cache on save
        cache.delete(f'user_profile:{self.user_id}')
        
        # Resize avatar efficiently
        if self.avatar and hasattr(self.avatar, 'path'):
            try:
                img = Image.open(self.avatar.path)
                if img.height > 300 or img.width > 300:
                    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    img.save(self.avatar.path, optimize=True, quality=85)
            except Exception:
                pass


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    name = models.CharField(max_length=250, db_index=True)
    email = models.EmailField(db_index=True)
    subject = models.CharField(max_length=250)
    message = models.TextField(max_length=3000)
    is_resolved = models.BooleanField(default=False, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = ContactManager()

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_resolved', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.created_at.date()}"


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    duration_minutes = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'code']),
        ]

    def __str__(self):
        return self.name
    
    @classmethod
    def get_cached_active_services(cls):
        cache_key = 'active_services_list'
        services = cache.get(cache_key)
        
        if services is None:
            services = list(
                cls.objects.filter(is_active=True)
                .only('id', 'name', 'code', 'price')
                .order_by('name')
            )
            cache.set(cache_key, services, 86400) # 24 hours
        
        return services


class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments', db_index=True)
    service = models.CharField(max_length=100, choices=SERVICE_CHOICES, db_index=True)
    doctor_email = models.EmailField(db_index=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    date = models.DateField(db_index=True)
    time = models.CharField(max_length=5, choices=TIME_SLOTS, db_index=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    calendar_created_at = models.DateTimeField(null=True, blank=True)

    objects = AppointmentManager()

    class Meta:
        ordering = ['-date', '-time']
        # indexes = [
        #     models.Index(fields=['user', 'status', 'date']),
        #     models.Index(fields=['date', 'time', 'doctor_email']),
        #     models.Index(fields=['doctor_email', 'date', 'status']),
        # ]
        indexes = [
            # For slot availability checks
            models.Index(
                fields=['doctor_email', 'date', 'status'],
                name='idx_slot_lookup'
            ),
            # For user appointments
            models.Index(
                fields=['user', '-date'],
                name='idx_user_appointments'
            ),
            # For reminder tasks
            models.Index(
                fields=['date', 'status'],
                name='idx_reminder_scan'
            ),
        ]
        unique_together = [['date', 'time', 'doctor_email']]
        
    def __str__(self):
        return f"Appt#{self.id} - {self.date} {self.time}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Invalidate relevant caches
        cache.delete(f'slots:{self.date}:{self.doctor_email}')
        cache.delete(f'sidebar_appt:{self.user_id}')
        cache.delete(f'user_appointment_stats:{self.user_id}')


class Newsletter(models.Model):
    email = models.EmailField(unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['is_active', 'subscribed_at']),
        ]

    def __str__(self):
        return self.email



@receiver(post_save, sender=Appointment)
def update_appointment_metrics(sender, instance, **kwargs):
    """Update appointment metrics on save"""
    from django.db.models import Count
    
    # Count appointments by status
    stats = Appointment.objects.values('status').annotate(count=Count('id'))
    
    for stat in stats:
        active_appointments.labels(status=stat['status']).set(stat['count'])

