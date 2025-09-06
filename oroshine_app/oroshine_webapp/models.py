from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# Phone number validator
phone_validator = RegexValidator(
    regex=r'^\+?\d{10,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

# User Profile
class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True, validators=[phone_validator])
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, validators=[phone_validator])

    def __str__(self):
        return f"{self.user.username} Profile"


# Contact inquiries
class Contact(models.Model):
    name = models.CharField(max_length=250)
    email = models.EmailField()
    subject = models.CharField(max_length=250)
    message = models.TextField(max_length=3000)
    is_read = models.BooleanField(default=False)
    replied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


# Appointments
class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.CharField(max_length=100)
    doctor_email = models.EmailField()
    name = models.CharField(max_length=100)
    email = models.EmailField()
    date = models.DateField()
    time = models.TimeField()
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('doctor_email', 'date', 'time')
        indexes = [
            models.Index(fields=['doctor_email', 'date', 'time']),  # Fast filtering for bookings
            models.Index(fields=['date']),  # Quick daily queries
        ]
        constraints = [
            models.UniqueConstraint(fields=['doctor_email', 'date', 'time'], name='unique_appointment_slot')
        ]

    def __str__(self):
        return f"{self.name} - {self.service} ({self.date} {self.time})"
