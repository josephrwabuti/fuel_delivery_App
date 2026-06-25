from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


@login_required
def provider_home(request):
    context = {
        "today_orders": 7,
        "active_orders": 2,
        "total_litres_today": 480,
        "revenue_today": "1.4M",
        "pending_orders": [],
        "recent_orders": [],
        "stock_levels": [],
        "active_drivers": [],
    }
    return render(request, "provider/home.html", context)


@login_required
def provider_orders(request):
    return render(request, "provider/orders.html")


@login_required
def provider_stock(request):
    return render(request, "provider/stock.html")

@login_required
def provider_update_stock(request):
    return render(request, "provider/stock.html")

@login_required
def provider_restock(request):
    return render(request, "provider/stock.html")


@login_required
def provider_drivers(request):
    return render(request, "provider/drivers.html")

@login_required
def provider_add_driver(request):
    return render(request, "provider/drivers.html")


@login_required
def provider_reports(request):
    return render(request, "provider/reports.html")


@login_required
def provider_order_detail(request, order_id):
    return HttpResponse(f"Order {order_id}")


@login_required
def provider_accept_order(request, order_id):
    return HttpResponse(f"Accepted Order {order_id}")


@login_required
def provider_reject_order(request, order_id):
    return HttpResponse(f"Rejected Order {order_id}")

@login_required
def provider_demand(request):
    return render(request, "provider/demand.html")


@login_required
def provider_station(request):
    return render(request, "provider/station.html")

@login_required
def provider_update_station(request):
    return render(request, "provider/station.html")

@login_required
def provider_profile(request):
    return render(request, "provider/profile.html")

@login_required
def provider_update_profile(request):
    return render(request, "provider/profile.html")

@login_required
def provider_change_password(request):
    return render(request, "provider/profile.html")