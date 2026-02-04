from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile,Appointment,TIME_SLOTS,Doctor,Service
from .services_cache import get_service_tuples
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from django.utils import timezone
from datetime import timedelta



class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = [
            'phone', 'date_of_birth', 'address', 'city', 'state', 
            'zip_code', 'avatar', 'emergency_contact_name', 
            'emergency_contact_phone', 'medical_history', 'allergies'
        ]
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+91 (555) 123-4567'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': '123 Main Street'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Mumbai'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Maharashtra'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '441107'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control', 
                'accept': 'image/*'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'John Doe'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+1 (555) 987-6543'
            }),
            'medical_history': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Any relevant medical history...'
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'List any allergies...'
            }),
        }

    def clean_avatar(self):
        """Validate and compress avatar image"""
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Check file size (2MB limit)
            if avatar.size > 1 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 2MB )")
            
            # Check file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            ext = avatar.name.split('.')[-1].lower()
            if f'.{ext}' not in valid_extensions:
                raise forms.ValidationError("Unsupported file extension. Use JPG, PNG, or GIF.")
            
            try:
                # Compress and resize image
                img = Image.open(avatar)
                
                # Convert RGBA to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Resize if too large
                if img.height > 800 or img.width > 800:
                    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                
                # Save to BytesIO
                output = BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                output.seek(0)
                
                # Create new InMemoryUploadedFile
                avatar = InMemoryUploadedFile(
                    output, 'ImageField', 
                    f"{avatar.name.split('.')[0]}.jpg",
                    'image/jpeg', 
                    sys.getsizeof(output), 
                    None
                )
            except Exception as e:
                raise forms.ValidationError(f"Error processing image: {str(e)}")
        
        return avatar


    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile.save()
        
        return profile





class ServiceForm(forms.ModelForm):
    """
    Admin form for managing services.
    Can be used in Django admin or custom views.
    """
    
    class Meta:
        model = Service
        fields = [
            'name', 'code', 'description', 'price', 'duration_minutes',
            'display_order', 'icon', 'color', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., root_canal'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '15',
                'max': '240'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'fa-tooth'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_code(self):
        """Ensure code is unique and slug-friendly"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.lower().replace(' ', '_')
        return code







class AppointmentForm(forms.ModelForm):
    """
    Appointment form with dynamic Service dropdown.
    Services are loaded from database instead of hardcoded choices.
    """
    
    # Override service field to use ForeignKey instead of CharField
    service = forms.ModelChoiceField(
        queryset=Service.objects.none(),  # Will be set in __init__
        empty_label="Select a Service",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True,
        }),
        help_text="Choose the dental service you need"
    )
    
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.none(),  # Will be set in __init__
        empty_label="Select a Doctor",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True,
        })
    )
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': timezone.now().date().isoformat(),
            'max': (timezone.now().date() + timedelta(days=365)).isoformat(),
        })
    )
    
    time = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True,
        })
    )
    
    class Meta:
        model = Appointment
        fields = ['service', 'doctor', 'name', 'email', 'phone', 'date', 'time', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Any special requirements or notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set queryset for services (only active services)
        self.fields['service'].queryset = Service.cached_active_services()
        
        # Set queryset for doctors (only active doctors)
        self.fields['doctor'].queryset = Doctor.cached_active_doctors()
        
        # Pre-fill user data if available
        if user and user.is_authenticated:
            self.fields['name'].initial = user.get_full_name() or user.username
            self.fields['email'].initial = user.email
            
            # Try to get phone from profile
            try:
                profile = user.profile
                if profile.phone:
                    self.fields['phone'].initial = profile.phone
            except:
                pass
        
        # Set time choices from TIME_SLOTS in models
        from .models import TIME_SLOTS
        self.fields['time'].choices = [('', 'Select Time')] + list(TIME_SLOTS)
    
    def clean_date(self):
        """Validate appointment date"""
        date = self.cleaned_data.get('date')
        
        if date < timezone.now().date():
            raise ValidationError('Appointment date cannot be in the past')
        
        max_date = timezone.now().date() + timedelta(days=365)
        if date > max_date:
            raise ValidationError('Cannot book appointments more than 1 year in advance')
        
        return date
    
    def clean_service(self):
        """Validate service is active"""
        service = self.cleaned_data.get('service')
        
        if service and not service.is_active:
            raise ValidationError('This service is no longer available')
        
        return service
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        
        # Check for double booking
        if doctor and date and time:
            existing = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time=time,
                status__in=['pending', 'confirmed']
            )
            
            # Exclude current appointment if editing
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    f'This time slot is already booked. Please choose another time.'
                )
        
        return cleaned_data
