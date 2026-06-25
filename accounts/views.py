from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Profile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def customer_home(request):
    return render(request, "customer/home.html")

def register(request):

    if request.method == "POST":

        role = request.POST.get("role")

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        phone = request.POST.get("phone")
        license_number = request.POST.get("license_number")
        license_no = request.POST.get("license_no")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("login")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already exists")
            return redirect("login")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )

        Profile.objects.create(
            user=user,
            role=role,
            phone=phone,
            license_number=license_number,
            license_no=license_no,
        )

        messages.success(request, "Account created successfully")

        return redirect("login")

    return render(request, "accounts/login_register.html")


def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            login(request, user)

            profile = Profile.objects.get(user=user)

            if profile.role == "customer":
                return redirect("customer_home")

            elif profile.role == "provider":
                return redirect("provider_home")

            elif profile.role == "driver":
                return redirect("driver_home")

            elif profile.role == "admin":
                return redirect("admin_dashboard")

        messages.error(request, "Invalid email or password")
        return redirect("login")

    return render(request, "accounts/login_register.html")

def forgot_password(request):
    return render(request, "accounts/forgot_password.html")

    
def logout_view(request):
    logout(request)
    return redirect("login")