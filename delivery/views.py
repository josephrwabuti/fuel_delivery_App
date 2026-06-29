from django.shortcuts import render


def driver_orders(request):
    return render(request, "driver/orders.html")


def driver_active(request):
    return render(request, "driver/active.html")


def driver_earnings(request):
    return render(request, "driver/earnings.html")


def driver_history(request):
    return render(request, "driver/history.html")

def driver_profile(request):
    return render(request, "driver/profile.html")

def driver_notifications(request):
    return render(request, "driver/notifications.html")

def driver_update_profile(request):
    return render(request, "driver/profile.html")

def driver_change_password(request):
    return render(request, "driver/profile.html")