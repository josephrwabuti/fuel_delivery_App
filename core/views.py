from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import role_required
from orders.forms import OrderForm
from accounts.models import Station, Driver, CustomerProfile
from orders.models import Order
from delivery.models import DeliveryLog
from core.models import Notification, PlatformSettings
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
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

        price_map = {
            "Petrol": 2850,
            "Diesel": 2700,
            "Kerosene": 2600
        }

        price_per_litre = price_map.get(fuel_type, 2850)
        total_price = price_per_litre * float(quantity) + 2000

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


# ===========================
#  ADMIN HELPERS
# ===========================

def get_admin_base_context():
    pending_stations = Station.objects.filter(status="pending").count()
    pending_drivers = Driver.objects.filter(status="pending").count()
    notif_count = 0
    return {
        "pending_stations": pending_stations,
        "pending_drivers": pending_drivers,
        "notif_count": notif_count,
    }


# ===========================
#  ADMIN DASHBOARD
# ===========================

@login_required(login_url='login')
@role_required('admin')
def admin_home(request):
    ctx = get_admin_base_context()
    today = timezone.now().date()

    total_orders_today = Order.objects.filter(created_at__date=today).count()
    active_stations = Station.objects.filter(status="approved").count()
    active_drivers = Driver.objects.filter(is_approved=True).count()
    on_duty_drivers = Driver.objects.filter(on_duty=True).count()
    total_customers = User.objects.filter(role="customer").count()
    live_deliveries = Order.objects.filter(
        status__in=["confirmed", "assigned", "picked_up", "delivering"]
    ).count()
    revenue_today = Order.objects.filter(
        created_at__date=today, status="delivered"
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    pending_station_list = Station.objects.filter(status="pending")
    pending_driver_list = Driver.objects.filter(status="pending")

    total_orders = Order.objects.count()
    total_stations = Station.objects.count()
    total_drivers = Driver.objects.count()
    total_revenue = Order.objects.filter(
        status="delivered"
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    ctx.update({
        "total_orders_today": total_orders_today,
        "active_stations": active_stations,
        "active_drivers": active_drivers,
        "on_duty_drivers": on_duty_drivers,
        "total_customers": total_customers,
        "live_deliveries": live_deliveries,
        "revenue_today": int(revenue_today),
        "pending_station_list": pending_station_list,
        "pending_driver_list": pending_driver_list,
        "total_orders": total_orders,
        "total_stations": total_stations,
        "total_drivers": total_drivers,
        "total_revenue": int(total_revenue),
    })

    return render(request, 'admin_panel/home.html', ctx)


# ===========================
#  ADMIN STATIONS
# ===========================

@login_required(login_url='login')
@role_required('admin')
def admin_stations(request):
    ctx = get_admin_base_context()

    pending_stations = Station.objects.filter(status='pending')
    approved_stations = Station.objects.filter(status='approved')
    rejected_stations = Station.objects.filter(status='rejected')

    ctx.update({
        'pending_stations': pending_stations,
        'approved_stations': approved_stations,
        'rejected_stations': rejected_stations,
        'stations': Station.objects.all(),
        'pending_count': pending_stations.count(),
        'approved_count': approved_stations.count(),
        'rejected_count': rejected_stations.count(),
        'total_count': Station.objects.count(),
    })

    return render(request, 'admin_panel/stations.html', ctx)


@login_required
@role_required("admin")
def approve_station(request, station_id):
    station = get_object_or_404(Station, id=station_id)
    station.status = "approved"
    station.save()

    Notification.objects.create(
        user=station.owner,
        title="Station Approved",
        message=f"Your station '{station.name}' has been approved by the admin.",
    )

    return JsonResponse({"success": True})


@login_required
@role_required("admin")
def reject_station(request, station_id):
    station = get_object_or_404(Station, id=station_id)
    station.status = "rejected"
    station.save()

    if request.method == "POST":
        messages.success(request, f"{station.name} rejected.")
        return redirect("admin_stations")

    return JsonResponse({"success": True})


# ===========================
#  ADMIN DRIVERS
# ===========================

@login_required(login_url='login')
@role_required('admin')
def admin_drivers(request):
    ctx = get_admin_base_context()
    drivers = User.objects.filter(role="driver").select_related("driver")

    approved_drivers = drivers.filter(driver__status="approved").count()
    pending_drivers = drivers.filter(driver__status="pending").count()
    rejected_drivers = drivers.filter(driver__status="rejected").count()
    active_drivers = drivers.filter(driver__on_duty=True).count()

    ctx.update({
        "drivers": drivers,
        "approved_drivers": approved_drivers,
        "pending_drivers": pending_drivers,
        "rejected_drivers": rejected_drivers,
        "active_drivers": active_drivers,
    })
    return render(request, 'admin_panel/drivers.html', ctx)


@login_required
@role_required("admin")
def approve_driver(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    driver.is_approved = True
    driver.status = "approved"
    driver.save()

    Notification.objects.create(
        user=driver.user,
        title="Account Approved",
        message="Your driver account has been approved. You can now go On Duty and start receiving orders.",
    )

    return JsonResponse({"success": True})


@login_required
@role_required("admin")
def reject_driver(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    driver.is_approved = False
    driver.status = "rejected"
    driver.save()
    return JsonResponse({"success": True})


@login_required
@role_required("admin")
def suspend_driver(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    driver.status = "suspended"
    driver.is_approved = False
    driver.save()
    return JsonResponse({"success": True})


# ===========================
#  ADMIN CUSTOMERS
# ===========================

@login_required(login_url='login')
@role_required('admin')
def admin_customers(request):
    ctx = get_admin_base_context()
    customers = User.objects.filter(role="customer").annotate(
        order_count=Count("order"),
        total_spent=Sum("order__total_amount"),
    ).select_related("customerprofile")

    ctx["customers"] = customers
    return render(request, 'admin_panel/customers.html', ctx)


# ===========================
#  ADMIN ORDERS
# ===========================

@login_required(login_url='login')
@role_required('admin')
def admin_orders(request):
    ctx = get_admin_base_context()
    today = timezone.now().date()

    orders = Order.objects.select_related(
        "customer", "station", "driver"
    ).order_by("-created_at")

    pending_orders = orders.filter(status="pending").count()
    delivering_orders = orders.filter(
        status__in=["assigned", "picked_up", "delivering"]
    ).count()
    delivered_today = orders.filter(
        status="delivered", created_at__date=today
    ).count()
    total_orders = orders.count()

    ctx.update({
        "orders": orders,
        "pending_orders": pending_orders,
        "delivering_orders": delivering_orders,
        "delivered_today": delivered_today,
        "total_orders": total_orders,
    })
    return render(request, 'admin_panel/orders.html', ctx)


# ===========================
#  ADMIN REPORTS
# ===========================

@login_required(login_url='login')
@role_required('admin')
def admin_reports(request):
    ctx = get_admin_base_context()
    today = timezone.now().date()

    period_orders = Order.objects.count()
    period_litres = Order.objects.aggregate(total=Sum("quantity"))["total"] or 0
    period_revenue = Order.objects.filter(
        status="delivered"
    ).aggregate(total=Sum("total_amount"))["total"] or 0
    new_users = User.objects.filter(date_joined__date__gte=today - timezone.timedelta(days=30)).count()

    ctx.update({
        "period_orders": period_orders,
        "period_litres": period_litres,
        "period_revenue": int(period_revenue),
        "new_users": new_users,
    })
    return render(request, 'admin_panel/reports.html', ctx)


# ===========================
#  ADMIN MISC
# ===========================

def admin_demand(request):
    ctx = get_admin_base_context()
    return render(request, 'admin_panel/reports.html', ctx)


def admin_activity(request):
    ctx = get_admin_base_context()
    return render(request, 'admin_panel/activity.html', ctx)


@login_required(login_url='login')
@role_required('admin')
def admin_settings(request):
    ctx = get_admin_base_context()
    settings = PlatformSettings.objects.first()
    ctx["settings"] = settings
    return render(request, 'admin_panel/settings.html', ctx)


@login_required(login_url='login')
@role_required('admin')
def admin_save_settings(request):
    if request.method == "POST":
        settings, _ = PlatformSettings.objects.get_or_create(id=1)
        settings.platform_name = request.POST.get("platform_name", "FuelGo")
        settings.support_email = request.POST.get("support_email", "support@fuelgo.co.tz")
        settings.support_phone = request.POST.get("support_phone", "+255 700 000 000")
        settings.delivery_fee = request.POST.get("delivery_fee", 2000)
        settings.max_radius = request.POST.get("max_radius", 10)
        settings.order_timeout = request.POST.get("order_timeout", 15)
        settings.save()
        messages.success(request, "Settings saved successfully")
    return redirect("admin_settings")


@login_required(login_url='login')
@role_required('admin')
def admin_profile(request):
    ctx = get_admin_base_context()
    return render(request, 'admin_panel/profile.html', ctx)


@login_required(login_url='login')
@role_required('admin')
def admin_update_profile(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.phone = request.POST.get("phone", user.phone)
        user.save()
        messages.success(request, "Profile updated successfully")
    return redirect("admin_profile")


@login_required(login_url='login')
@role_required('admin')
def admin_change_password(request):
    if request.method == "POST":
        user = request.user
        old = request.POST.get("old_password")
        p1 = request.POST.get("password1")
        p2 = request.POST.get("password2")

        if not user.check_password(old):
            messages.error(request, "Current password is incorrect")
        elif p1 != p2:
            messages.error(request, "New passwords do not match")
        elif len(p1) < 8:
            messages.error(request, "Password must be at least 8 characters")
        else:
            user.set_password(p1)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully")

    return redirect("admin_profile")