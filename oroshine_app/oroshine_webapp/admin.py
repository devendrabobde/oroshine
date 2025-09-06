from django.contrib import admin
from .models import UserProfile, Contact, Appointment

# ============================
# UserProfile Admin
# ============================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'dob', 'gender', 'phone_number',
        'emergency_contact_name', 'emergency_contact_number'
    ]
    list_filter = ['gender']
    search_fields = ['user__username', 'user__email', 'phone_number', 'emergency_contact_name']
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Personal Info', {'fields': ('dob', 'gender', 'address', 'phone_number')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_number')}),
    )
    ordering = ['user__username']


# ============================
# Contact Admin
# ============================
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at', 'replied_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'replied_at']
    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} contact(s) marked as read.")
    mark_as_read.short_description = "Mark selected contacts as read"


# ============================
# Appointment Admin
# ============================
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'service', 'doctor_email', 'date', 'time', 'created_at']
    list_filter = ['service', 'doctor_email', 'date']
    search_fields = ['name', 'email', 'service', 'doctor_email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    date_hierarchy = 'date'

    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'email', 'service', 'doctor_email', 'date', 'time', 'message')
        }),
    )
