from django.contrib import admin
from .models import Contact, Appointment

# Register your models here.
admin.site.register(Contact)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'service', 'doctor_email', 'date', 'time', 'created_at']
    list_filter = ['service', 'date', 'doctor_email']
    search_fields = ['name', 'email', 'service']
    readonly_fields = ['created_at']
