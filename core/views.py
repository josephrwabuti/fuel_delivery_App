from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.decorators import role_required

def home(request):
    return render(request, 'core/index.html')


@login_required(login_url='login')
@role_required('customer')
def customer_dashboard(request):
    return render(request, 'customer/home.html')


@login_required(login_url='login')
@role_required('provider')
def provider_dashboard(request):
    return render(request, 'provider/home.html')


@login_required(login_url='login')
@role_required('driver')
def driver_dashboard(request):
    return render(request, 'driver/home.html')


@login_required(login_url='login')
@role_required('admin')
def admin_dashboard(request):
    return render(request, 'admin_panel/home.html')