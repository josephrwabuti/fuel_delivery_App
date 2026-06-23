from django.shortcuts import render
from django.http import HttpResponse

def customer_login(request):
    return HttpResponse("Customer Login")

def customer_register(request):
    return HttpResponse("Customer Register")

def provider_login(request):
    return HttpResponse("Provider Login")

def driver_login(request):
    return HttpResponse("Driver Login")

def admin_login(request):
    return HttpResponse("Admin Login")
