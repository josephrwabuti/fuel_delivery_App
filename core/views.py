from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import role_required
from orders.forms import OrderForm
from accounts.models import Station
from orders.models import Order
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
import json


def home(request):
    return render(request, 'core/index.html')


@login_required(login_url='login')
@role_required('customer')
def customer_home(request):

    nearby_stations = Station.objects.filter(
        status="approved"
    ).order_by("-created_at")[:6]

    recent_orders = Order.objects.filter(
        customer=request.user
    ).select_related("station").order_by("-created_at")[:5]

    last_order = Order.objects.filter(
        customer=request.user
    ).select_related("station").order_by("-created_at").first()

    active_order = Order.objects.filter(
        customer=request.user,
        status__in=[
            "pending",
            "confirmed",
            "driver_assigned",
            "en_route"
        ]
    ).select_related("driver", "station").first()

    total_orders = Order.objects.filter(
        customer=request.user
    ).count()

    delivered_orders = Order.objects.filter(
        customer=request.user,
        status="delivered"
    ).count()

    total_litres = Order.objects.filter(
        customer=request.user
    ).aggregate(total=Sum("quantity"))["total"] or 0

    context = {
        "nearby_stations": nearby_stations,
        "recent_orders": recent_orders,
        "last_order": last_order,
        "active_order": active_order,
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "total_litres": total_litres,
    }

    return render(request, "customer/home.html", context)


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

def stations_view(request):
    stations = Station.objects.prefetch_related("fuels").all()

    return render(request, "customer/stations.html", {
        "stations": stations,
        "stations_json": json.dumps([...])
    })


def create_order(request):
    station_id = request.GET.get("station")
    station = Station.objects.get(id=station_id)

    if request.method == "POST":
        order = Order.objects.create(
            customer=request.user,
            station=station,
            fuel_type=request.POST['fuel_type'],
            quantity=request.POST['quantity'],
            total_amount=request.POST['total_amount'],
            status="pending"
        )
        return redirect("customer_tracking")

    return render(request, "customer/order.html", {
        "station": station
    })


def tracking_view(request):
    active_order = Order.objects.filter(
        customer=request.user
    ).exclude(status="delivered").first()

    return render(request, "customer/tracking.html", {
        "active_order": active_order
    })


def history_view(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')

    return render(request, "customer/history.html", {
        "orders": orders
    })
    
def confirm_delivery(request, order_id):
    order = Order.objects.get(id=order_id, customer=request.user)

    if request.method == "POST":
        order.status = "delivered"
        order.save()

    return redirect("customer_tracking")


def cancel_order(request, order_id):
    order = Order.objects.get(id=order_id, customer=request.user)

    if request.method == "POST":
        order.status = "cancelled"
        order.save()

    return redirect("customer_tracking")


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


@login_required(login_url='login')
def customer_place_order(request):

    if request.method == "POST":

        station_id = request.POST.get("station_id")
        fuel_type = request.POST.get("fuel_type")
        quantity = request.POST.get("quantity")
        delivery_address = request.POST.get("delivery_address")
        phone = request.POST.get("contact_phone")

        station = get_object_or_404(Station, id=station_id)

        # simple pricing logic (same as JS)
        price_map = {
            "Petrol": 2850,
            "Diesel": 2700,
            "Kerosene": 2600
        }

        price_per_litre = price_map.get(fuel_type, 2850)
        total_price = price_per_litre * float(quantity) + 2000  # delivery fee

        order = Order.objects.create(
            customer=request.user,
            station=station,
            fuel_type=fuel_type,
            quantity=quantity,
            delivery_address=delivery_address,
            phone=phone,
            total_price=total_price,
            status="pending"
        )

        return redirect("customer_tracking")

    return redirect("customer_order")

@login_required(login_url='login')
@role_required('admin')
def admin_stations(request):

    pending_stations = Station.objects.filter(status='pending')
    approved_stations = Station.objects.filter(status='approved')
    rejected_stations = Station.objects.filter(status='rejected')

    return render(request, 'admin_panel/stations.html', {
        'pending_stations': pending_stations,
        'approved_stations': approved_stations,
        'rejected_stations': rejected_stations,
        'stations': Station.objects.all()  # optional for table loop
    })
    

@login_required
@role_required("admin")
def approve_station(request, station_id):

    station = get_object_or_404(Station, id=station_id)
    station.status = "approved"
    station.save()

    return JsonResponse({"success": True})


@login_required
def reject_station(request, station_id):

    station = get_object_or_404(Station, id=station_id)
    station.status = "rejected"
    station.save()

    return JsonResponse({"success": True})


def admin_drivers(request):
    return render(request, 'admin_panel/drivers.html')

def admin_customers(request):
    return render(request, 'admin_panel/customers.html')

def admin_orders(request):
    return render(request, 'admin_panel/orders.html')

def admin_reports(request):
    return render(request, 'admin_panel/reports.html')

def admin_demand(request):
    return render(request, 'admin_panel/reports.html')

def admin_activity(request):
    return render(request, 'admin_panel/activity.html')

def admin_settings(request):
    return render(request, 'admin_panel/settings.html')

def admin_profile(request):
    return render(request, 'admin_panel/profile.html')

def admin_save_settings(request):
    return render(request, 'admin_panel/settings.html')

def admin_update_profile(request):
    return render(request, 'admin_panel/profile.html')


def admin_change_password(request):
    return render(request, 'admin_panel/profile.html')