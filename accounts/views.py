from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Profile


def login_view(request):
    return render(request, "accounts/login_register.html")


def register_view(request):
    return render(request, "accounts/login_register.html")


def forgot_password(request):
    return render(request, "accounts/forgot_password.html")

def register(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        license_number = request.POST.get("license_number")
        license_no = request.POST.get("license_no")

        # clean spaces from JS formatting
        phone = phone.replace(" ", "")
        license_number = license_number.replace(" ", "")
        license_no = license_no.replace(" ", "")

        # Django model validation will handle limits automatically
        user = Profile.objects.create(
            phone=phone,
            license_number=license_number,
            license_no=license_no
        )

        return redirect("login")