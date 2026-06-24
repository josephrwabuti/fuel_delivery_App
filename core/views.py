from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'core/index.html')

# Customer dashboard
def customer_home(request):
    return render(request, "customer/home.html")

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
    return render(request, "customer/profile.html")

def customer_change_password(request):
    return render(request, "customer/profile.html")

def customer_delete_account(request):
    return render(request, "customer/profile.html")

def customer_place_order(request):
    return render(request, "customer/order.html")




