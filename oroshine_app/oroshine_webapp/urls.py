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
    # AJAX endpoints
    path("check_email/", views.check_email_availability, name="check_email_availability"),
    

]