from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Static pages
    path("", views.homepage, name="home"),
    path("about/", views.about, name="about"),
    path("appointment/", views.appointment, name="appointment"),
    path("contact/", views.contact, name="contact"),
    path("price/", views.price, name="price"),
    path("service/", views.service, name="service"),
    path("team/", views.team, name="team"),
    path("testimonial/", views.testimonial, name="testimonial"),
    
    # Authentication
    path("register/", views.register_request, name="register"),
    path("login/", views.login_request, name="login"),
    path("logout/", views.logout_request, name="logout"),
    
    # Profile management
    path("profile/", views.profile_view, name="profile"),
    path("profile/update/", views.profile_update, name="profile_update"),
    
    # Appointment management
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointment/success/", views.appointment_success, name="appointment_success"),
    
    # Password reset
    path("password_reset/", views.CustomPasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name="password_reset_complete"),
    
    # AJAX endpoints
    path("check_email/", views.check_email_availability, name="check_email_availability"),
    
    # Social Authentication
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('auth/success/', views.social_auth_success, name='social_auth_success'),

]