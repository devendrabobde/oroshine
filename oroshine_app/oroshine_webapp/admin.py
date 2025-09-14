from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import CustomUser, UserProfile, Contact, Appointment


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = '__all__'


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name')


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    extra = 0
    fieldsets = (
        ('Personal Information', {
            'fields': ('dob', 'gender', 'bio')
        }),
        ('Contact Information', {
            'fields': ('address', 'emergency_contact_name', 'emergency_contact_number')
        }),
        ('Additional', {
            'fields': ('website',)
        }),
    )


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'is_verified', 'is_staff', 'is_active', 'date_joined'
    )
    list_filter = (
        'is_staff', 'is_active', 'is_verified', 'date_joined', 'last_login'
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified',
                      'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 
                      'password1', 'password2'),
        }),
    )
    
    inlines = [UserProfileInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('profile')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'gender', 'dob', 'get_phone_number', 
        'emergency_contact_name', 'created_at'
    )
    list_filter = ('gender', 'created_at', 'updated_at')
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'emergency_contact_name'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Personal Information', {
            'fields': ('dob', 'gender', 'bio')
        }),
        ('Contact Information', {
            'fields': ('address', 'emergency_contact_name', 'emergency_contact_number')
        }),
        ('Additional', {
            'fields': ('website',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_phone_number(self, obj):
        return obj.user.phone_number
    get_phone_number.short_description = 'Phone Number'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'email', 'subject', 'is_read', 'created_at', 'replied_at'
    )
    list_filter = ('is_read', 'created_at', 'replied_at')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'subject')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('is_read', 'replied_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} contacts marked as read.')
    mark_as_read.short_description = 'Mark selected contacts as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} contacts marked as unread.')
    mark_as_unread.short_description = 'Mark selected contacts as unread'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'email', 'doctor_email', 'service', 
        'date', 'time', 'status', 'created_at'
    )
    list_filter = ('status', 'service', 'date', 'created_at')
    search_fields = (
        'name', 'email', 'doctor_email', 'service'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('user', 'name', 'email')
        }),
        ('Appointment Details', {
            'fields': ('doctor_email', 'service', 'date', 'time', 'status')
        }),
        ('Additional Information', {
            'fields': ('message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['confirm_appointments', 'cancel_appointments', 'complete_appointments']
    
    def confirm_appointments(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} appointments confirmed.')
    confirm_appointments.short_description = 'Confirm selected appointments'
    
    def cancel_appointments(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} appointments cancelled.')
    cancel_appointments.short_description = 'Cancel selected appointments'
    
    def complete_appointments(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} appointments marked as completed.')
    complete_appointments.short_description = 'Mark selected appointments as completed'


# Admin site customization
admin.site.site_header = "OroShine Dental Admin"
admin.site.site_title = "OroShine Admin Portal"
admin.site.index_title = "Welcome to OroShine Administration"