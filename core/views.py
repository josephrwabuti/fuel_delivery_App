from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.decorators import role_required

def home(request):
    return render(request, 'core/index.html')


@login_required(login_url='login')
@role_required('customer')
def customer_home(request):
    return render(request, 'customer/home.html')


@login_required(login_url='login')
@role_required('provider')
def provider_home(request):
    return render(request, 'provider/home.html')


@login_required(login_url='login')
@role_required('driver')
def driver_home(request):
    return render(request, 'driver/home.html')


@login_required(login_url='login')
@role_required('admin')
def admin_home(request):
    return render(request, 'admin_panel/home.html')

def customer_stations(request):
    return render(request, "customer/stations.html")


def customer_order(request):
    return render(request, "customer/order.html")


def customer_tracking(request):
    return render(request, "customer/tracking.html")


def customer_history(request):
    return render(request, "customer/history.html")

def customer_profile(request):
    return render(request, "customer/profile.html")

def customer_notifications(request):
    return render(request, "customer/notifications.html")

def customer_update_profile(request):
    return render(request, 'customer/profile.html')

def customer_change_password(request):
    return render(request, 'customer/profile.html')

def customer_delete_account(request):
    return render(request, 'customer/profile.html')

def customer_place_order(request):
    return render(request, 'customer/order.html')