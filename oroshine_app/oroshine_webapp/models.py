from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator, validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import uuid


# Phone number validator
phone_validator = RegexValidator(
    regex=r'^\+?\d{10,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)


class CustomUserManager(BaseUserManager):
    """Manager for CustomUser with email as the unique identifier."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Users must have an email address"))

        email = self.normalize_email(email)
        extra_fields.setdefault("username", email)  # always mirror email in username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("username", email)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Enhanced User model with email as username"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, blank=True, validators=[phone_validator])
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()  # Attach custom manager

    class Meta:
        db_table = 'custom_user'
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.lower()
            self.username = self.email  # Ensure username always matches email

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class UserProfile(models.Model):
    """Extended user profile for dental management"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    dob = models.DateField(null=True, blank=True, verbose_name='Date of Birth')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, validators=[phone_validator])
    bio = models.TextField(max_length=500, blank=True)

    # 🦷 Dental/Medical info
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True, help_text="List any known allergies")
    medical_conditions = models.TextField(blank=True, help_text="E.g., diabetes, hypertension")
    current_medications = models.TextField(blank=True)
    dental_history = models.TextField(blank=True, help_text="Past dental treatments, surgeries, issues")
    last_dental_visit = models.DateField(null=True, blank=True)
    insurance_provider = models.CharField(max_length=150, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

    def __str__(self):
        return f"{self.user.username}'s Profile"


class DentalRecord(models.Model):
    """Detailed dental visit records (per appointment)"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='dental_records')
    appointment = models.ForeignKey('Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    
    visit_date = models.DateField(auto_now_add=True)
    diagnosis = models.TextField(help_text="Doctor's diagnosis for this visit")
    treatment = models.TextField(help_text="Details of treatment performed")
    prescription = models.TextField(blank=True, help_text="Medicines prescribed")
    xray_image = models.ImageField(upload_to="dental/xrays/", null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes from doctor")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dental_record'
        ordering = ['-visit_date']
        verbose_name = _('Dental Record')
        verbose_name_plural = _('Dental Records')

    def __str__(self):
        return f"Dental Record - {self.user.email} ({self.visit_date})"


class Contact(models.Model):
    """Contact inquiries"""
    name = models.CharField(max_length=250)
    email = models.EmailField()
    subject = models.CharField(max_length=250)
    message = models.TextField(max_length=3000)
    is_read = models.BooleanField(default=False)
    replied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contact'
        ordering = ['-created_at']
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Appointment(models.Model):
    """Appointments with enhanced validation"""
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.CharField(max_length=100)
    doctor_email = models.EmailField()
    name = models.CharField(max_length=100)
    email = models.EmailField()
    date = models.DateField()
    time = models.TimeField()
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled'),
            ('completed', 'Completed'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointment'
        ordering = ['-created_at']
        unique_together = ('doctor_email', 'date', 'time')
        indexes = [
            models.Index(fields=['doctor_email', 'date', 'time']),
            models.Index(fields=['date']),
            models.Index(fields=['user']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['doctor_email', 'date', 'time'],
                name='unique_appointment_slot'
            )
        ]
        verbose_name = _('Appointment')
        verbose_name_plural = _('Appointments')

    def clean(self):
        super().clean()
        if self.email:
            try:
                validate_email(self.email)
            except ValidationError:
                raise ValidationError({'email': 'Enter a valid email address.'})

        if self.doctor_email:
            try:
                validate_email(self.doctor_email)
            except ValidationError:
                raise ValidationError({'doctor_email': 'Enter a valid doctor email address.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.service} ({self.date} {self.time})"



