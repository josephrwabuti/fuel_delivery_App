from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .models import CustomerProfile, Driver, Station
from django.contrib.auth.models import User


def login_dispatch(request):
    if request.method == "POST":
        role = request.POST.get("role")
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if not user:
            return render(request, "accounts/login_register.html", {
                "error": "Invalid credentials",
                "initial_role": role
            })

        # CUSTOMER
        if role == "customer" and hasattr(user, "customerprofile"):
            login(request, user)
            return redirect("customer_home")

        # DRIVER
        if role == "driver" and hasattr(user, "driver"):
            login(request, user)
            return redirect("driver_home")

        # PROVIDER
        if role == "provider" and hasattr(user, "station"):
            login(request, user)
            return redirect("provider_home")

        # ADMIN
        if role == "admin" and user.is_staff:
            login(request, user)
            return redirect("admin_home")

        return render(request, "accounts/login_register.html", {
            "error": "Role mismatch or invalid account",
            "initial_role": role
        })

    return render(request, "accounts/login_register.html")

def register_dispatch(request):
    if request.method == "POST":
        role = request.POST.get("role")

        # ================= CUSTOMER =================
        if role == "customer":
            user = User.objects.create_user(
                username=request.POST["email"],
                email=request.POST["email"],
                password=request.POST["password1"],
                first_name=request.POST["first_name"],
                last_name=request.POST["last_name"],
            )

            CustomerProfile.objects.create(
                user=user,
                phone=request.POST.get("phone", "")
            )

            return redirect("/accounts/login/")

        # ================= DRIVER =================
        if role == "driver":
            user = User.objects.create_user(
                username=request.POST["email"],
                email=request.POST["email"],
                password=request.POST["password1"],
                first_name=request.POST["first_name"],
                last_name=request.POST["last_name"],
            )

            Driver.objects.create(
                user=user,
                phone=request.POST["phone"],
                licence_number=request.POST.get("license_no", ""),
                status="pending",
                is_approved=False,
            )

            return redirect("login_dispatch")

        # ================= PROVIDER =================
        if role == "provider":
            user = User.objects.create_user(
                username=request.POST["email"],
                email=request.POST["email"],
                password=request.POST["password1"],
                first_name=request.POST["first_name"],
                last_name=request.POST["last_name"],
            )

            Station.objects.create(
                owner=user,
                name=request.POST["station_name"],
                address=request.POST["station_address"],
                lat=request.POST["station_lat"],
                lng=request.POST["station_lng"],
                status="pending",
                is_approved=False,
            )

            return redirect("login_dispatch")

    return render(request, "accounts/login_register.html")


def forgot_password(request):
    return render(request, "accounts/forgot_password.html")