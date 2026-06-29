from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User

User = get_user_model()


def login_view(request):

    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:
            login(request, user)

            if user.role == "customer":
                return redirect("customer_home")

            elif user.role == "provider":
                return redirect("provider_home")

            elif user.role == "driver":
                return redirect("driver_home")

            elif user.role == "admin":
                return redirect("admin_home")

        messages.error(request, "Invalid email or password")

    return render(request, "accounts/login_register.html")


def register(request):
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password1']
        role = request.POST.get('role', 'customer')

        if User.objects.filter(username=email).exists():
            messages.error(request, "User already exists")
            return redirect('register')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role
        )

        messages.success(request, "Account created successfully")
        return redirect('login')

    return render(request, "accounts/login_register.html")


def logout_view(request):
    logout(request)
    return redirect('login')

def forgot_password(request):
    return render(request, "accounts/login_register.html")