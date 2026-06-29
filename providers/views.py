from django.shortcuts import render

def provider_home(request):
    return render(request, "provider/home.html")


def provider_orders(request):
    return render(request, "provider/orders.html")


def provider_stock(request):
    return render(request, "provider/stock.html")


def provider_drivers(request):
    return render(request, "provider/drivers.html")


def provider_reports(request):
    return render(request, "provider/reports.html")


def provider_order_detail(request, id):
    return render(request, "provider/order_detail.html")


def provider_accept_order(request, id):
    return render(request, "provider/orders.html")


def provider_reject_order(request, id):
    return render(request, "provider/orders.html")

def provider_demand(request):
    return render(request, "provider/demand.html")

def provider_station(request):
    return render(request, "provider/station.html")

def provider_profile(request):
    return render(request, "provider/profile.html")

def provider_update_stock(request):
    return render(request, "provider/stock.html")

def provider_restock(request):
    return render(request, "provider/stock.html")

def provider_add_driver(request):
    return render(request, "provider/drivers.html")

def provider_update_station(request):
    return render(request, "provider/station.html")

def provider_update_profile(request):
    return render(request, "provider/profile.html")

def provider_change_password(request):
    return render(request, "provider/profile.html")