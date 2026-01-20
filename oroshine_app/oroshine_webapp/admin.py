from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    Contact,
    Appointment,
    UserProfile,
    Service,
    Doctor
)

# ===============================
# USER PROFILE ADMIN
# ===============================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'phone',
        'city',
        'created_at',
        'avatar_preview'
    )
    list_filter = ('city', 'state', 'created_at')
    search_fields = (
        'user__username',
        'user__email',
        'phone',
        'city'
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'avatar_preview'
    )

    fieldsets = (
        ('User Info', {
            'fields': ('user', 'phone', 'date_of_birth')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'zip_code')
        }),
        ('Medical', {
            'fields': (
                'emergency_contact_name',
                'emergency_contact_phone',
                'medical_history',
                'allergies'
            )
        }),
        ('Avatar', {
            'fields': ('avatar', 'avatar_preview')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:50%;" />',
                obj.avatar.url
            )
        return "No Image"

    avatar_preview.short_description = "Avatar"


# ===============================
# CONTACT ADMIN
# ===============================

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'email',
        'subject',
        'is_resolved',
        'created_at'
    )
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('created_at', 'resolved_at')
    actions = ('mark_resolved',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    @admin.action(description="Mark selected messages as resolved")
    def mark_resolved(self, request, queryset):
        queryset.update(
            is_resolved=True,
            resolved_at=timezone.now()
        )


# ===============================
# DOCTOR ADMIN
# ===============================

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'specialization',
        'is_active',
        'display_order'
    )
    list_filter = ('is_active', 'specialization')
    search_fields = ('full_name', 'email', 'specialization')
    list_editable = ('is_active', 'display_order')
    ordering = ('display_order', 'full_name')


# ===============================
# SERVICE ADMIN
# ===============================

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'price',
        'is_active'
    )
    list_editable = ('price', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)


# ===============================
# APPOINTMENT ADMIN
# ===============================

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'doctor',
        'service',
        'date',
        'time',
        'status_badge'
    )

    list_filter = (
        'status',
        'date',
        'doctor',
        'service'
    )

    search_fields = (
        'user__username',
        'user__email',
        'name',
        'email',
        'phone'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'email_sent_at',
        'calendar_created_at'
    )

    actions = (
        'mark_confirmed',
        'mark_cancelled',
        'mark_completed'
    )

    date_hierarchy = 'date'
    ordering = ('-date', '-time')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user',
            'doctor'
        )

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#28a745',
            'cancelled': '#dc3545',
            'completed': '#6c757d'
        }
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;border-radius:4px;">{}</span>',
            colors.get(obj.status, '#333'),
            obj.get_status_display()
        )

    status_badge.short_description = "Status"

    @admin.action(description="Mark as Confirmed")
    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')

    @admin.action(description="Mark as Cancelled")
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')

    @admin.action(description="Mark as Completed")
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
