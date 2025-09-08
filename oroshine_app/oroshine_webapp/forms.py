from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Appointment,Contact,UserProfile
from datetime import date
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import logging
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
logger = logging.getLogger(__name__)



class ContactForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Your Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Your Email'})
    )
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Subject'})
    )
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'placeholder': 'Your Message'})
    )

    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError("Invalid email address")
        return email





class NewUserForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    
    dob = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=UserProfile.GENDER_CHOICES, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Address'}), required=False)
    phone_number = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'placeholder': 'Contact Number'}))
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Emergency Contact Name'}))
    emergency_contact_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'placeholder': 'Emergency Contact Number'}))

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "dob", "gender", "address",
                  "phone_number", "emergency_contact_name", "emergency_contact_number", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            
            UserProfile.objects.create(
                user=user,
                dob=self.cleaned_data.get('dob'),
                gender=self.cleaned_data.get('gender'),
                address=self.cleaned_data.get('address'),
                phone_number=self.cleaned_data.get('phone_number'),
                emergency_contact_name=self.cleaned_data.get('emergency_contact_name'),
                emergency_contact_number=self.cleaned_data.get('emergency_contact_number'),
            )
        return user


class UserProfileForm(forms.ModelForm):
    dob = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))
    gender = forms.ChoiceField(choices=UserProfile.GENDER_CHOICES, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows':2}), required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    emergency_contact_name = forms.CharField(max_length=100, required=False)
    emergency_contact_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 
                  'dob', 'gender', 'address', 'phone_number',
                  'emergency_contact_name', 'emergency_contact_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Update Profile'))







class AppointmentForm(forms.ModelForm):
    """
    Appointment form with enhanced validation logging
    """
    class Meta:
        model = Appointment
        fields = ['name', 'email', 'doctor_email', 'service', 'date', 'time', 'message']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email or "@" not in email:
            logger.warning(f"Invalid patient email attempted: {email}")
            raise forms.ValidationError("Enter a valid patient email address.")
        return email

    def clean_doctor_email(self):
        doctor_email = self.cleaned_data.get('doctor_email')
        if not doctor_email or "@" not in doctor_email:
            logger.warning(f"Invalid doctor email attempted: {doctor_email}")
            raise forms.ValidationError("Enter a valid doctor email address.")
        return doctor_email

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        service = cleaned_data.get('service')

        logger.info(f"Validating appointment: date={date}, time={time}, service={service}")

        if not date or not time:
            logger.error("Missing date or time during form validation")
            raise forms.ValidationError("Date and time must be provided.")

        return cleaned_data