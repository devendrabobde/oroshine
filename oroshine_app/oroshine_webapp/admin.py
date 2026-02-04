# admin.py - Django admin for managing dynamic services

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    Service, Doctor, Appointment, Contact, 
    UserProfile, Newsletter
)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    Admin interface for managing dental services.
    Allows adding, editing, and reordering services.
    """
    list_display = [
        'name', 'code', 'colored_icon', 'price_display', 
        'duration_display', 'appointment_count', 'is_active', 
        'display_order'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['display_order', 'name']
    readonly_fields = ['ulid', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'ulid')
        }),
        ('Pricing & Duration', {
            'fields': ('price', 'duration_minutes')
        }),
        ('Display Settings', {
            'fields': ('display_order', 'icon', 'color', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def colored_icon(self, obj):
        """Display icon with color"""
        if obj.icon:
            return format_html(
                '<i class="{}" style="color: {}; font-size: 20px;"></i>',
                obj.icon,
                obj.color
            )
        return '-'
    colored_icon.short_description = 'Icon'
    
    def price_display(self, obj):
        """Format price with currency symbol"""
        return f"₹{obj.price:,.2f}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'
    
    def duration_display(self, obj):
        """Display duration in readable format"""
        hours = obj.duration_minutes // 60
        minutes = obj.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        return f"{minutes}m"
    duration_display.short_description = 'Duration'
    duration_display.admin_order_field = 'duration_minutes'
    
    def appointment_count(self, obj):
        """Count appointments for this service"""
        count = obj.appointments.count()
        if count > 0:
            return format_html(
                '<a href="/admin/appointments/appointment/?service__ulid={}">{} appointments</a>',
                obj.ulid,
                count
            )
        return '0'
    appointment_count.short_description = 'Appointments'
    
    def get_queryset(self, request):
        """Optimize queryset with annotation"""
        qs = super().get_queryset(request)
        return qs.annotate(appt_count=Count('appointments'))
    
    actions = ['activate_services', 'deactivate_services']
    
    def activate_services(self, request, queryset):
        """Bulk activate services"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} service(s) activated.')
    activate_services.short_description = 'Activate selected services'
    
    def deactivate_services(self, request, queryset):
        """Bulk deactivate services"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} service(s) deactivated.')
    deactivate_services.short_description = 'Deactivate selected services'


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """Admin interface for doctors"""
    list_display = ['full_name', 'email', 'specialization', 'is_active', 'display_order']
    list_filter = ['is_active', 'specialization']
    search_fields = ['full_name', 'email']
    ordering = ['display_order', 'full_name']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin interface for appointments"""
    list_display = [
        'ulid_short', 'name', 'service_display', 'doctor', 
        'date', 'time', 'status', 'created_at'
    ]
    list_filter = ['status', 'date', 'service', 'doctor']
    search_fields = ['name', 'email', 'phone', 'ulid']
    readonly_fields = ['ulid', 'created_at', 'updated_at', 'email_sent_at', 'calendar_created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Appointment Info', {
            'fields': ('ulid', 'user', 'service', 'doctor', 'date', 'time', 'status')
        }),
        ('Patient Details', {
            'fields': ('name', 'email', 'phone', 'message')
        }),
        ('System Fields', {
            'fields': ('calendar_event_id', 'created_at', 'updated_at', 'email_sent_at', 'calendar_created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def ulid_short(self, obj):
        """Display shortened ULID"""
        return f"{obj.ulid[:8]}..."
    ulid_short.short_description = 'ULID'
    
    def service_display(self, obj):
        """Display service with color"""
        if obj.service:
            return format_html(
                '<span style="color: {};">{}</span>',
                obj.service.color,
                obj.service.name
            )
        return '-'
    service_display.short_description = 'Service'
    service_display.admin_order_field = 'service__name'
    
    actions = ['mark_as_confirmed', 'mark_as_completed', 'mark_as_cancelled']
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} appointment(s) confirmed.')
    mark_as_confirmed.short_description = 'Mark as Confirmed'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} appointment(s) completed.')
    mark_as_completed.short_description = 'Mark as Completed'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} appointment(s) cancelled.')
    mark_as_cancelled.short_description = 'Mark as Cancelled'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin interface for contact submissions"""
    list_display = ['ulid_short', 'name', 'email', 'subject', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['ulid', 'created_at']
    date_hierarchy = 'created_at'
    
    def ulid_short(self, obj):
        return f"{obj.ulid[:8]}..."
    ulid_short.short_description = 'ULID'
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{updated} contact(s) marked as resolved.')
    mark_as_resolved.short_description = 'Mark as Resolved'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for user profiles"""
    list_display = ['user', 'phone', 'city', 'created_at']
    list_filter = ['city', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin interface for newsletter subscriptions"""
    list_display = ['email', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']