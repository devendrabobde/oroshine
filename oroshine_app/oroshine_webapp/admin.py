from django.contrib import admin
from django.utils.html import format_html
from .models import Contact, Appointment, UserProfile, Service

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'created_at', 'avatar_preview']
    list_filter = ['city', 'state', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'city']
    readonly_fields = ['created_at', 'updated_at', 'avatar_preview']
    
    # Optimization: prevents N+1 query for the User table
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    fieldsets = (
        ('User Information', {'fields': ('user', 'phone', 'date_of_birth')}),
        ('Address', {'fields': ('address', 'city', 'state', 'zip_code')}),
        ('Medical', {'fields': ('emergency_contact_name', 'emergency_contact_phone', 'medical_history', 'allergies')}),
        ('Visuals', {'fields': ('avatar', 'avatar_preview')}),
    )

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%;" />', obj.avatar.url)
        return "No Img"


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['created_at', 'resolved_at']
    actions = ['mark_resolved']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_resolved=True, resolved_at=timezone.now())
    mark_resolved.short_description = "Mark selected messages as Resolved"


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_link', 'doctor_email', 'service', 'date', 'time', 'status_badge']
    list_filter = ['status', 'date', 'doctor_email', 'service']
    search_fields = ['name', 'email', 'phone', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['confirm_appt', 'cancel_appt', 'complete_appt']
    date_hierarchy = 'date'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def user_link(self, obj):
        return obj.user.username
    user_link.short_description = 'User'

    def status_badge(self, obj):
        colors = {'pending': '#ffc107', 'confirmed': '#28a745', 'cancelled': '#dc3545', 'completed': '#6c757d'}
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; border-radius:3px;">{}</span>',
            colors.get(obj.status, '#333'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def confirm_appt(self, request, queryset): queryset.update(status='confirmed')
    def cancel_appt(self, request, queryset): queryset.update(status='cancelled')
    def complete_appt(self, request, queryset): queryset.update(status='completed')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'price', 'is_active')
    list_editable = ('price', 'is_active')
    search_fields = ('name', 'code')