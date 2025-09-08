from django.urls import path, include
from . import views  #importing our view file 

urlpatterns = [
    path("", views.homepage, name="home"), 
    path("about", views.about, name="about"),
    path("appointment", views.appointment, name="appointment"),
    path("contact", views.contact, name="contact"),
    path("price", views.price, name="price"),
    path("service", views.service, name="service"),
    path("team", views.team, name="team"),
    path("testimonial", views.testimonial, name="testimonial"),
    # User Profile
    path('profile/', views.profile_view, name='profile'),
     # Authentication URLs
    path("check-email/", views.check_email_availability, name="check_email"),
    path("register", views.register_request, name="register"),
    path("login", views.login_request, name="login"),
    path("logout", views.logout_request, name="logout"),
     # Google & other social logins (from django-allauth)
    path("accounts/", include("allauth.urls")),
]
