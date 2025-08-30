from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Appointment
from datetime import date


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


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["service", "doctor_email", "name", "email", "date", "time", "message"]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'min': date.today()}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional Message (Optional)'}),
        }

    def clean_date(self):
        appointment_date = self.cleaned_data.get('date')
        if appointment_date and appointment_date < date.today():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        return appointment_date