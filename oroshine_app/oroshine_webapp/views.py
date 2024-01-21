from django.shortcuts import render, redirect
from .forms import NewUserForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib import messages
from django.core.mail import send_mail
from .models import Contact

# Create your views here.

def homepage(request):
  	return render(request, 'index.html', context={})

def about(request):
  	return render(request, 'about.html', context={})

def appointment(request):
  	return render(request, 'appointment.html', context={})

def contact(request):
	if request.method == 'POST':
		contact = Contact()
		name = request.POST.get('name')
		email = request.POST.get('email')
		subject = request.POST.get('subject')
		message = request.POST.get('message')
		contact.name = name
		contact.email = email
		contact.subject = subject
		contact.message = message
		contact.save()
		subject_to_send = "Welcome to OroShine Dental Care"
		message_to_send = "Our team will contact you within 24hrs."
		email_from = "info@oroshinedentalcare.com"
		recipient_list = email
		send_mail(subject_to_send, message_to_send, email_from, [recipient_list])
		messages.success(request, "Thank you for contacting us." )
		return redirect("/")
	return render (request, 'contact.html', context={})

def price(request):
  	return render(request, 'price.html', context={})

def service(request):
  	return render(request, 'service.html', context={})

def team(request):
  	return render(request, 'team.html', context={})

def testimonial(request):
  	return render(request, 'testimonial.html', context={})

def register_request(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, "Registration successful." )
			return redirect("/")
		messages.error(request, "Unsuccessful registration. Invalid information.")
	form = NewUserForm()
	return render (request=request, template_name="register.html", context={"register_form":form})

def login_request(request):
	if request.method == "POST":
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				messages.success(request, f"You are now logged in as {username}.")
				messages.success(request, "Login successful." )
				return redirect("/")
			else:
				messages.error(request,"Invalid username or password.")
		else:
			messages.error(request,"Invalid username or password.")
	form = AuthenticationForm()
	return render(request=request, template_name="login.html", context={"login_form":form})

def logout_request(request):
	logout(request)
	messages.success(request, "You have successfully logged out.") 
	return redirect("/")
