from django.urls import path, include
from django.contrib import admin

from . import views

urlpatterns = [

    # alredy register in app/urls.py
    # path('admin/', admin.site.urls),
    path("accounts/", include("allauth.urls")),

    # ==========================================
    # MAIN PAGES
    # ==========================================
    
    path("", views.homepage, name="home"), 
    path("about/", views.about, name="about"),
    path("appointment/", views.appointment, name="appointment"),
    path("contact/", views.contact, name="contact"),
    path("price/", views.price, name="price"),
    path("service/", views.service, name="service"),
    path("team/", views.team, name="team"),
    path("testimonial/", views.testimonial, name="testimonial"),
    path("newsletter/", views.newsletter, name="newsletter"),

    # ==========================================
    # AUTHENTICATION
    # ==========================================
    path("custom-register/", views.register_request, name="custom_register"),
    path("custom-login/", views.login_request, name="custom_login"),
    path("custom-logout/", views.logout_request, name="custom_logout"),
    
    # Social authentication (django-allauth)
    
    # ==========================================
    # USER PROFILE
    # ==========================================
    path("profile/", views.user_profile, name="user_profile"),
    
    # ==========================================
    # AJAX ENDPOINTS
    # ==========================================
    path("api/check-slots/", views.check_available_slots, name="check_slots_ajax"),
    path("api/book-appointment/", views.book_appointment_ajax, name="book_appointment_ajax"),
    path("api/login/", views.login_ajax, name="login_ajax"),
    path("api/check-availability/", views.check_availability, name="check_availability"),
]

