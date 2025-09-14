from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta
import logging
from .models import CustomUser, UserProfile, Appointment, Contact

logger = logging.getLogger(__name__)


class CustomUserCreationForm(UserCreationForm):
    """Enhanced user registration form"""
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (Optional)'
        })
    )
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        }),
        strip=False
    )
    
    # Profile fields
    dob = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Date of Birth'
    )
    gender = forms.ChoiceField(
        choices=[('', 'Select Gender')] + UserProfile.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Address (Optional)'
        }),
        required=False
    )
    emergency_contact_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Emergency Contact Name (Optional)'
        })
    )
    emergency_contact_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Emergency Contact Number (Optional)'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'username', 'email', 'phone_number',
            'password1', 'password2'
        )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError(_("A user with this email already exists."))
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = username.lower().strip()
            if CustomUser.objects.filter(username=username).exists():
                raise ValidationError(_("A user with this username already exists."))
        return username
    
    def clean_dob(self):
        dob = self.cleaned_data.get('dob')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 13:
                raise ValidationError(_("You must be at least 13 years old to register."))
            if dob > today:
                raise ValidationError(_("Date of birth cannot be in the future."))
        return dob
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            phone = phone.strip()
            if len(phone) < 10:
                raise ValidationError(_("Phone number must be at least 10 digits."))
        return phone


class CustomAuthenticationForm(AuthenticationForm):
    """Enhanced login form"""
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = username.lower().strip()
        return username
    
    def clean(self):
        email = self.cleaned_data.get('username')  # username field contains email
        password = self.cleaned_data.get('password')
        
        if email and password:
            # Authenticate using email
            try:
                user_obj = CustomUser.objects.get(email=email)
                user = authenticate(self.request, username=user_obj.username, password=password)
            except CustomUser.DoesNotExist:
                user = None
            
            if not user:
                logger.warning(f"Failed login attempt for: {email}")
                raise ValidationError(_("Invalid email or password."))
            
            if not user.is_active:
                raise ValidationError(_("This account is inactive."))
            
            self.user_cache = user
        
        return self.cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = UserProfile
        fields = ['dob', 'gender', 'address', 'emergency_contact_name', 
                 'emergency_contact_number', 'bio', ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['phone_number'].initial = user.phone_number


class CustomPasswordResetForm(PasswordResetForm):
    """Enhanced password reset form"""
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if not CustomUser.objects.filter(email=email, is_active=True).exists():
                raise ValidationError(_("No active user found with this email address."))
        return email





class ContactForm(forms.ModelForm):
    """Contact form with enhanced validation"""
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email'
        })
    )
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Your Message',
            'rows': 5
        })
    )
    
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError(_("Enter a valid email address."))
        return email
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if message and len(message.strip()) < 10:
            raise ValidationError(_("Message must be at least 10 characters long."))
        return message


class AppointmentForm(forms.ModelForm):
    """Enhanced appointment form"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email'
        })
    )
    doctor_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Doctor Email'
        })
    )
    service = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Service Required'
        })
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Additional Message (Optional)',
            'rows': 3
        })
    )
    
    class Meta:
        model = Appointment
        fields = ['name', 'email', 'doctor_email', 'service', 'date', 'time', 'message']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            try:
                validate_email(email)
            except ValidationError:
                logger.warning(f"Invalid patient email attempted: {email}")
                raise forms.ValidationError(_("Enter a valid patient email address."))
        return email
    
    def clean_doctor_email(self):
        doctor_email = self.cleaned_data.get('doctor_email')
        if doctor_email:
            doctor_email = doctor_email.lower().strip()
            try:
                validate_email(doctor_email)
            except ValidationError:
                logger.warning(f"Invalid doctor email attempted: {doctor_email}")
                raise forms.ValidationError(_("Enter a valid doctor email address."))
        return doctor_email
    
    def clean_date(self):
        appointment_date = self.cleaned_data.get('date')
        if appointment_date:
            today = date.today()
            if appointment_date < today:
                raise ValidationError(_("Appointment date cannot be in the past."))
            
            # Don't allow appointments more than 3 months in advance
            max_date = today + timedelta(days=90)
            if appointment_date > max_date:
                raise ValidationError(_("Appointments can only be booked up to 3 months in advance."))
        
        return appointment_date
    
    def clean(self):
        cleaned_data = super().clean()
        date_val = cleaned_data.get('date')
        time_val = cleaned_data.get('time')
        doctor_email = cleaned_data.get('doctor_email')
        
        logger.info(f"Validating appointment: date={date_val}, time={time_val}, doctor={doctor_email}")
        
        if date_val and time_val and doctor_email:
            # Check for existing appointments
            existing = Appointment.objects.filter(
                doctor_email=doctor_email,
                date=date_val,
                time=time_val
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                logger.warning(f"Appointment slot conflict: {doctor_email} - {date_val} {time_val}")
                raise ValidationError(_("This appointment slot is already booked."))
        
        return cleaned_data


