from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from bigBallz import settings
from django.core.mail import send_mail
import win32com.client as win32
import pythoncom
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from . tokens import generate_token
from django.template.loader import render_to_string
def home(request):
	return render(request, "authentication/index.html")

def signup(request):
	
	if request.method == "POST":

		username = request.POST.get('username')
		fname = request.POST.get('fname')
		lname = request.POST.get('lname')
		email = request.POST.get('email')
		password1 = request.POST.get('password1')
		password2 = request.POST.get('password2')

		if User.objects.filter(username = username):
			messages.error(request, "Username already exists!  Please try another.")
			return redirect('home')

		if User.objects.filter(email = email):
			messages.error(request, "Email already registered!  Please try another.")
			return redirect('home')

		if len(username) > 15:
			messages.error(request, "Username is too long!  Please try another. (15 max)")
			return redirect('home')
		
		if len(username) < 6:
			messages.error(request, "Username is too short!  Please try another. (at least 5)")
			return redirect('home')

		if password1 != password2:
			messages.error(request,"Passwors didn't match!")


		myuser = User.objects.create_user(username, email, password1)
		myuser.first_name = fname
		myuser.last_name = lname
		myuser.is_active = False

		myuser.save()

		messages.success(request, "Your Account has been successfully created!  We have sent you a confirmation email, please confirm your email in order to activate your account.")

		#Welcome Email

		olApp = win32.Dispatch('Outlook.Application',pythoncom.CoInitialize())
		olNS = olApp.GetNameSpace('MAPI')

		mail_item = olApp.createItem(0)

		mail_item.Subject = "Welcome to Big Ballz League"
		mail_item.BodyFormat = 1

		mail_item.Body = "Hello" + myuser.first_name + "!! \n" + "Welcome to The Big Ballz League!! \n Thank you for joining our waitlist \n We have also sent you a confirmation email, please confirm your email address in order to activate your account! \n\n Thank You, \n League Commissioner"
		mail_item.Sender = "commissioner@bigballzdfsl.com"
		mail_item.To = myuser.email

		mail_item.Display()
		mail_item.Save()
		mail_item.Send()

		#Email Address Confirmation Email

		mail_item1 = olApp.createItem(0)

		current_site = get_current_site(request)
		mail_item1.Subject = "Confirm your email for The Big Ballz Leage!"
		mail_item1.BodyFormat = 1
		mail_item1.Body = render_to_string('authentication/email_confirmation.html',{
			'name' : myuser.first_name,
			'domain' : current_site.domain,
			'uid' : urlsafe_base64_encode(force_bytes(myuser.pk)),
			'token' : generate_token.make_token(myuser),
			})
		mail_item1.Sender = "commissioner@bigballzdfsl.com"
		mail_item1.To = myuser.email

		#email.fail_silently = True

		#mail_item1.Display()
		mail_item1.Save()
		mail_item1.Send()

		return redirect('signin')

	return render(request,"authentication/signup.html")	


def signin(request):

	if request.method == 'POST':
		username = request.POST.get('username')
		password1 = request.POST.get('password1')

		user = authenticate(username = username, password = password1)

		if user is not None:
			login(request, user)
			fname = user.first_name
			return render(request, "authentication/index.html", {'fname': fname})

		else:
			messages.error(request, "Bad Credentials!")
			return redirect('home')	

	return render(request, "authentication/signin.html")

def signout(request):
	logout(request)
	messages.success(request, "Logged Out Successfully")
	return redirect('home')

def activate(request, uidb64, token):
	try:
		uid = force_str(urlsafe_base64_decode(uidb64))
		myuser = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist):
		myuser = None

	if myuser is not None and generate_token.check_token(myuser,token):
		myuser.is_active = True
		myuser.save()
		login(request, myuser)
		return redirect('signin')
	else:
		return render(request, 'authentication/activation_failed.html')	

def sample(request):
	return render(request,"authentication/sample.html")