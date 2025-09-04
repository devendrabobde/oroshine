from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Appointment
from datetime import date
import logging
logger = logging.getLogger(__name__)


# Create your forms here.

class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")

	def save(self, commit=True):
		user = super(NewUserForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user


# class AppointmentForm(forms.ModelForm):
#     class Meta:
#         model = Appointment
#         fields = ["service", "doctor_email", "name", "email", "date", "time", "message"]
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date', 'min': date.today()}),
#             'time': forms.TimeInput(attrs={'type': 'time'}),
#             'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional Message (Optional)'}),
#         }

#     def clean_date(self):
#         appointment_date = self.cleaned_data.get('date')
#         if appointment_date and appointment_date < date.today():
#             raise forms.ValidationError("Appointment date cannot be in the past.")
#         return appointment_date



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