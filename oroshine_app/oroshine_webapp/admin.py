from django.contrib import admin
from django.utils.html import format_html
from .models import Contact, Appointment, UserProfile, TimeSlot


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'created_at', 'avatar_preview']
    list_filter = ['city', 'state', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'city']
    readonly_fields = ['created_at', 'updated_at', 'avatar_preview']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone', 'date_of_birth')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'zip_code')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Medical Information', {
            'fields': ('medical_history', 'allergies')
        }),
        ('Profile Picture', {
            'fields': ('avatar', 'avatar_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="100" height="100" style="border-radius: 50%;" />', obj.avatar.url)
        return "No avatar"
    avatar_preview.short_description = 'Avatar Preview'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_resolved', 'created_at', 'user_link']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'user', 'resolved_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('user', 'name', 'email', 'subject')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('is_resolved', 'resolved_at')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['mark_as_resolved', 'mark_as_unresolved']

    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/auth/user/{}/change/">{}</a>', obj.user.id, obj.user.username)
        return "Anonymous"
    user_link.short_description = 'User'

    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{updated} contact(s) marked as resolved.')
    mark_as_resolved.short_description = 'Mark selected as resolved'

    def mark_as_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False, resolved_at=None)
        self.message_user(request, f'{updated} contact(s) marked as unresolved.')
    mark_as_unresolved.short_description = 'Mark selected as unresolved'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'service', 'doctor_email', 'date', 'time', 'status', 'created_at', 'status_badge']
    list_filter = ['status', 'service', 'date', 'doctor_email', 'created_at']
    search_fields = ['name', 'email', 'phone', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'user', 'calendar_event_id']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('user', 'name', 'email', 'phone')
        }),
        ('Appointment Details', {
            'fields': ('service', 'doctor_email', 'date', 'time', 'message')
        }),
        ('Status', {
            'fields': ('status', 'calendar_event_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['confirm_appointments', 'cancel_appointments', 'mark_completed']

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#28a745',
            'cancelled': '#dc3545',
            'completed': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def confirm_appointments(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} appointment(s) confirmed.')
    confirm_appointments.short_description = 'Confirm selected appointments'

    def cancel_appointments(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} appointment(s) cancelled.')
    cancel_appointments.short_description = 'Cancel selected appointments'

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} appointment(s) marked as completed.')
    mark_completed.short_description = 'Mark as completed'


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['time', 'formatted_time', 'is_active']
    list_filter = ['is_active']
    ordering = ['time']
    
    def formatted_time(self, obj):
        return obj.time.strftime('%I:%M %p')
    formatted_time.short_description = 'Formatted Time'