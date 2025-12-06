from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
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
    path("register/", views.register_request, name="register"),
    path("login/", views.login_request, name="login"),
    path("logout/", views.logout_request, name="logout"),
    
    # Social authentication (django-allauth)
    path('accounts/', include('allauth.urls')),
    
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
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)