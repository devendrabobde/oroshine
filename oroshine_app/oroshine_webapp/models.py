from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image


class UserProfile(models.Model):
    """Extended user profile for dental clinic patients"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    medical_history = models.TextField(max_length=1000, blank=True)
    allergies = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Resize avatar if too large
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.avatar.path)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'phone']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contacts')
    name = models.CharField(max_length=250, db_index=True)
    email = models.EmailField(db_index=True)
    subject = models.CharField(max_length=250)
    message = models.TextField(max_length=3000)
    is_resolved = models.BooleanField(default=False, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

    class Meta:
        indexes = [
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['is_resolved', 'created_at']),
        ]
        ordering = ['-created_at']


class TimeSlot(models.Model):
    """Pre-defined time slots for appointments"""
    SLOT_CHOICES = [
        ('09:00', '09:00 AM'),
        ('09:30', '09:30 AM'),
        ('10:00', '10:00 AM'),
        ('10:30', '10:30 AM'),
        ('11:00', '11:00 AM'),
        ('11:30', '11:30 AM'),
        ('12:00', '12:00 PM'),
        ('14:00', '02:00 PM'),
        ('14:30', '02:30 PM'),
        ('15:00', '03:00 PM'),
        ('15:30', '03:30 PM'),
        ('16:00', '04:00 PM'),
        ('16:30', '04:30 PM'),
        ('17:00', '05:00 PM'),
    ]
    time = models.TimeField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.time.strftime('%I:%M %p')

    class Meta:
        ordering = ['time']


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    SERVICE_CHOICES = [
        ('checkup', 'General Checkup'),
        ('cleaning', 'Teeth Cleaning'),
        ('filling', 'Dental Filling'),
        ('extraction', 'Tooth Extraction'),
        ('root_canal', 'Root Canal'),
        ('whitening', 'Teeth Whitening'),
        ('braces', 'Braces Consultation'),
        ('emergency', 'Emergency'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    service = models.CharField(max_length=100, choices=SERVICE_CHOICES, db_index=True)
    doctor_email = models.EmailField(db_index=True)
    name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=15)
    date = models.DateField(db_index=True)
    time = models.TimeField(db_index=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.service} ({self.date} {self.time})"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['service', 'doctor_email', 'date']),
            models.Index(fields=['date', 'time', 'doctor_email']),
            models.Index(fields=['status', 'date']),
        ]
        unique_together = [['date', 'time', 'doctor_email']]  # Prevent double booking



class AppointmentHistory(models.Model):
    """
    Track appointment changes for audit trail
    Helps debug race conditions and conflicts
    """
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(max_length=50)  # created, updated, cancelled
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    old_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20, blank=True, null=True)
    old_date = models.DateField(blank=True, null=True)
    new_date = models.DateField(blank=True, null=True)
    old_time = models.TimeField(blank=True, null=True)
    new_time = models.TimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Appointment History'
        verbose_name_plural = 'Appointment Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['appointment', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self):
        return f"{self.action} - {self.appointment} at {self.created_at}"


class BookingLock(models.Model):
    """
    Distributed lock table for appointment booking
    Alternative to Redis locks for simpler deployments
    """
    lock_key = models.CharField(max_length=255, unique=True)
    locked_by = models.CharField(max_length=255)
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Booking Lock'
        verbose_name_plural = 'Booking Locks'
        indexes = [
            models.Index(fields=['lock_key', 'expires_at']),
        ]

    def __str__(self):
        return f"Lock: {self.lock_key}"

    @classmethod
    def acquire_lock(cls, lock_key, timeout=10):
        """Try to acquire a lock"""
        from django.db import transaction
        from django.utils import timezone
        
        try:
            with transaction.atomic():
                # Clean expired locks
                cls.objects.filter(
                    lock_key=lock_key,
                    expires_at__lt=timezone.now()
                ).delete()
                
                # Try to create new lock
                lock = cls.objects.create(
                    lock_key=lock_key,
                    locked_by=f"booking_{timezone.now().timestamp()}",
                    expires_at=timezone.now() + timedelta(seconds=timeout)
                )
                return lock
        except:
            return None

    @classmethod
    def release_lock(cls, lock_key):
        """Release a lock"""
        cls.objects.filter(lock_key=lock_key).delete()


class Newsletter(models.Model):
    """Newsletter subscriptions"""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Newsletter Subscription'
        verbose_name_plural = 'Newsletter Subscriptions'
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['email', 'is_active']),
        ]

    def __str__(self):
        return self.email