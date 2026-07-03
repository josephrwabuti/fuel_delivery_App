from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import role_required
from orders.forms import OrderForm
from accounts.models import Station, Driver, CustomerProfile
from orders.models import Order
from delivery.models import DeliveryLog
from core.models import Notification, PlatformSettings
from django.contrib.auth import get_user_model

User = get_user_model()
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, Avg, F, Value, FloatField
from django.db.models.functions import TruncDate, ExtractWeekDay
from django.utils import timezone
from django.utils.timesince import timesince
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from datetime import timedelta
import json


def home(request):
    return render(request, 'core/index.html')


@login_required(login_url='login')
@role_required('customer')
def customer_home(request):

    nearby_stations = Station.objects.filter(
        status="approved", is_open=True
    ).prefetch_related("fuels").order_by("-created_at")[:6]

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
            "assigned",
            "out",
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

    today = timezone.now()
    hour = today.hour
    if hour < 12:
        time_of_day = "Morning"
    elif hour < 17:
        time_of_day = "Afternoon"
    else:
        time_of_day = "Evening"

    delivered = Order.objects.filter(customer=request.user, status="delivered")
    avg_seconds = delivered.exclude(confirmed_at=None).annotate(
        diff=F("delivered_at") - F("confirmed_at")
    ).aggregate(avg=Avg("diff"))["avg"]
    avg_delivery_time = int(avg_seconds.total_seconds() / 60) if avg_seconds else None

    context = {
        "nearby_stations": nearby_stations,
        "recent_orders": recent_orders,
        "last_order": last_order,
        "active_order": active_order,
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "total_litres": total_litres,
        "time_of_day": time_of_day,
        "avg_delivery_time": avg_delivery_time,
    }

    return render(request, "customer/home.html", context)


@login_required(login_url='login')
@role_required('provider')
def provider_home(request):
    return render(request, 'provider/home.html')


@login_required(login_url='login')
@role_required('customer')
def stations_view(request):
    stations = Station.objects.filter(status="approved", is_open=True).prefetch_related("fuels")

    stations_list = []
    for s in stations:
        fuels = []
        for f in s.fuels.all():
            fuels.append({
                "type": f.type,
                "price": f"{f.price:,.0f}",
                "ok": f.available,
            })
        stations_list.append({
            "id": s.id,
            "name": s.name,
            "address": s.address,
            "lat": s.lat,
            "lng": s.lng,
            "status": s.status,
            "is_open": s.is_open,
            "rating": str(s.rating),
            "reviews": str(s.review_count),
            "hours": s.hours or "24/7",
            "phone": s.phone or "—",
            "fuels": fuels,
        })

    return render(request, "customer/stations.html", {
        "stations": stations,
        "stations_json": json.dumps(stations_list),
    })


@login_required(login_url='login')
@role_required('customer')
def create_order(request):
    station_id = request.GET.get("station")
    reorder_id = request.GET.get("reorder")
    preselected_station = None

    if reorder_id:
        prev_order = get_object_or_404(Order, id=reorder_id, customer=request.user)
        preselected_station = prev_order.station
    elif station_id:
        preselected_station = get_object_or_404(Station, id=station_id)

    if preselected_station and not preselected_station.is_open:
        messages.error(request, f"'{preselected_station.name}' is currently closed. Please choose an open station.")
        return redirect("customer_stations")

    if request.method == "POST":
        station = preselected_station
        if station and not station.is_open:
            messages.error(request, "Cannot place order — station is closed.")
            return redirect("customer_stations")
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
        "preselected_station": preselected_station
    })


def tracking_view(request):
    active_order = Order.objects.filter(
        customer=request.user
    ).exclude(status="delivered").select_related("station", "driver").first()

    return render(request, "customer/tracking.html", {
        "active_order": active_order
    })


def history_view(request):
    orders = Order.objects.filter(customer=request.user).select_related("station", "driver").order_by('-created_at')

    orders_list = []
    for o in orders:
        orders_list.append({
            "id": o.id,
            "station": o.station.name if o.station else "—",
            "fuel_type": o.fuel_type,
            "quantity": o.quantity,
            "total_amount": f"{o.total_amount:,.0f}",
            "status": o.status,
            "status_display": o.get_status_display(),
            "delivery_address": o.delivery_address or "—",
            "driver": o.driver.name if o.driver else "—",
            "payment_method": o.payment_method or "—",
            "created_at": o.created_at.strftime("%d %b %Y"),
        })

    return render(request, "customer/history.html", {
        "orders": orders,
        "orders_json": json.dumps(orders_list),
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
    total_orders = Order.objects.filter(customer=request.user).count()
    delivered_orders = Order.objects.filter(customer=request.user, status="delivered").count()
    total_litres = Order.objects.filter(customer=request.user).aggregate(total=Sum("quantity"))["total"] or 0
    return render(request, "customer/profile.html", {
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "total_litres": total_litres,
    })

def customer_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    unread_notifications = notifications.filter(is_read=False)
    read_notifications = notifications.filter(is_read=True)
    from django.utils.timesince import timesince
    for n in unread_notifications:
        n.time_since = timesince(n.created_at) + " ago"
    for n in read_notifications:
        n.time_since = timesince(n.created_at) + " ago"
    return render(request, "customer/notifications.html", {
        "notifications": notifications,
        "unread_notifications": unread_notifications,
        "read_notifications": read_notifications,
        "unread_count": unread_notifications.count(),
    })

def customer_update_profile(request):
    total_orders = Order.objects.filter(customer=request.user).count()
    delivered_orders = Order.objects.filter(customer=request.user, status="delivered").count()
    total_litres = Order.objects.filter(customer=request.user).aggregate(total=Sum("quantity"))["total"] or 0
    return render(request, 'customer/profile.html', {
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "total_litres": total_litres,
    })

def customer_change_password(request):
    total_orders = Order.objects.filter(customer=request.user).count()
    delivered_orders = Order.objects.filter(customer=request.user, status="delivered").count()
    total_litres = Order.objects.filter(customer=request.user).aggregate(total=Sum("quantity"))["total"] or 0
    return render(request, 'customer/profile.html', {
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "total_litres": total_litres,
    })

def customer_delete_account(request):
    total_orders = Order.objects.filter(customer=request.user).count()
    delivered_orders = Order.objects.filter(customer=request.user, status="delivered").count()
    total_litres = Order.objects.filter(customer=request.user).aggregate(total=Sum("quantity"))["total"] or 0
    return render(request, 'customer/profile.html', {
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "total_litres": total_litres,
    })


@login_required(login_url='login')
def dismiss_notification(request, notif_id):
    if request.method == "POST":
        Notification.objects.filter(id=notif_id, user=request.user).delete()
    return JsonResponse({"success": True})


@login_required(login_url='login')
def mark_all_notifications_read(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"success": True})


@login_required(login_url='login')
def customer_place_order(request):

    if request.method == "POST":

        station_id = request.POST.get("station_id")
        fuel_type = request.POST.get("fuel_type")
        quantity = request.POST.get("quantity")
        delivery_address = request.POST.get("delivery_address", "")
        phone = request.POST.get("phone", "")

        station = get_object_or_404(Station, id=station_id)
        if not station.is_open:
            messages.error(request, "Cannot place order — station is currently closed.")
            return redirect("customer_stations")

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
            total_amount=total_price,
            status="pending"
        )

        return redirect("customer_tracking")

    return redirect("customer_order")


# ===========================
#  ADMIN HELPERS
# ===========================

def get_admin_base_context(request=None):
    pending_stations = Station.objects.filter(status="pending").count()
    pending_drivers = Driver.objects.filter(status="pending").count()
    user_notifs = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10] if request and request.user.is_authenticated else []
    notif_count = sum(1 for n in user_notifs if not n.is_read)
    notifs_json = []
    for n in user_notifs:
        notifs_json.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'time': timesince(n.created_at) + ' ago',
        })
    return {
        "pending_stations": pending_stations,
        "pending_drivers": pending_drivers,
        "notif_count": notif_count,
        "notifs_json": json.dumps(notifs_json),
    }


# ===========================
#  ADMIN DASHBOARD
# ===========================

@login_required(login_url='login')
@role_required('admin')
def admin_home(request):
    ctx = get_admin_base_context(request)
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

    start_of_week = today - timedelta(days=today.weekday())
    week_days = []
    week_labels = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        count = Order.objects.filter(created_at__date=day).count()
        week_labels.append(day.strftime('%a'))
        week_days.append({'label': day.strftime('%a'), 'count': count})
    max_count = max((d['count'] for d in week_days), default=1)

    top_stations = Station.objects.annotate(
        order_count=Count('order')
    ).filter(order_count__gt=0).order_by('-order_count')[:5]

    recent_orders_list = Order.objects.select_related(
        'customer', 'station', 'driver'
    ).order_by('-created_at')[:5]

    delivered_orders = Order.objects.filter(status='delivered')
    total_delivered = delivered_orders.count()
    avg_delivery_seconds = delivered_orders.exclude(
        confirmed_at=None
    ).annotate(
        diff=F('delivered_at') - F('confirmed_at')
    ).aggregate(avg=Avg('diff'))['avg']
    avg_delivery = int(avg_delivery_seconds.total_seconds() / 60) if avg_delivery_seconds else 0
    total_all = total_orders or 1
    delivery_rate = int((total_delivered / total_all) * 100)

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
        "week_days": week_days,
        "week_max": max_count,
        "week_labels": week_labels,
        "top_stations": top_stations,
        "recent_orders_list": recent_orders_list,
        "avg_delivery": avg_delivery,
        "delivery_rate": delivery_rate,
    })

    return render(request, 'admin_panel/home.html', ctx)


# ===========================
#  ADMIN STATIONS
# ===========================

@login_required(login_url='login')
@role_required('admin')
def admin_stations(request):
    ctx = get_admin_base_context(request)

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
    ctx = get_admin_base_context(request)
    drivers = User.objects.filter(role="driver").select_related("driver")

    approved_drivers = drivers.filter(driver__status="approved").count()
    pending_drivers = drivers.filter(driver__status="pending").count()
    assigned_drivers = drivers.filter(driver__status="assigned").count()
    rejected_drivers = drivers.filter(driver__status="rejected").count()
    active_drivers = drivers.filter(driver__on_duty=True).count()

    ctx.update({
        "drivers": drivers,
        "approved_drivers": approved_drivers,
        "pending_drivers": pending_drivers,
        "assigned_drivers": assigned_drivers,
        "rejected_drivers": rejected_drivers,
        "active_drivers": active_drivers,
        "stations": Station.objects.filter(status="approved"),
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
        message="Your driver account has been approved. An admin will assign you to a station soon.",
    )

    return JsonResponse({"success": True})


@login_required
@role_required("admin")
def assign_driver_station(request, driver_id):
    if request.method == "POST":
        driver = get_object_or_404(Driver, id=driver_id)
        station_id = request.POST.get("station_id")
        station = get_object_or_404(Station, id=station_id)
        driver.station = station
        driver.status = "assigned"
        driver.is_approved = True
        driver.save()

        Notification.objects.create(
            user=driver.user,
            title="Station Assigned",
            message=f"You have been assigned to {station.name}. Please coordinate with the station owner.",
        )

        Notification.objects.create(
            user=station.owner,
            title="New Driver Assigned",
            message=f"Driver {driver.name} has been assigned to your station by the admin. Please accept or reject.",
        )

        return JsonResponse({"success": True, "station_name": station.name})
    return JsonResponse({"success": False}, status=400)


@login_required
@role_required("admin")
def reject_driver(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    driver.is_approved = False
    driver.status = "rejected"
    driver.save()

    Notification.objects.create(
        user=driver.user,
        title="Account Rejected",
        message="Your driver account has been rejected. Please contact support for more information.",
    )

    return JsonResponse({"success": True})


@login_required
@role_required("admin")
def suspend_driver(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    driver.status = "suspended"
    driver.is_approved = False
    driver.save()

    Notification.objects.create(
        user=driver.user,
        title="Account Suspended",
        message="Your driver account has been suspended. Please contact support for more information.",
    )

    return JsonResponse({"success": True})


# ===========================
#  ADMIN CUSTOMERS
# ===========================

@login_required(login_url='login')
@role_required('admin')
def admin_customers(request):
    ctx = get_admin_base_context(request)
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
    ctx = get_admin_base_context(request)
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
    ctx = get_admin_base_context(request)
    today = timezone.now().date()

    period = int(request.GET.get('period', 7))
    since = today - timedelta(days=period)
    period_qs = Order.objects.filter(created_at__date__gte=since)

    period_orders = period_qs.count()
    period_litres = period_qs.aggregate(total=Sum("quantity"))["total"] or 0
    period_revenue = period_qs.filter(
        status="delivered"
    ).aggregate(total=Sum("total_amount"))["total"] or 0
    new_users = User.objects.filter(date_joined__date__gte=today - timedelta(days=30)).count()

    week_start = today - timedelta(days=today.weekday())
    report_week = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        count = Order.objects.filter(created_at__date=day).count()
        report_week.append({'label': day.strftime('%a'), 'count': count})
    report_max = max((d['count'] for d in report_week), default=1)

    fuel_totals = Order.objects.values('fuel_type').annotate(
        total=Count('id')
    ).order_by()
    fuel_orders = Order.objects.count() or 1
    fuel_data = {}
    for f in fuel_totals:
        fuel_data[f['fuel_type']] = int((f['total'] / fuel_orders) * 100)

    top_stations = Station.objects.annotate(
        order_count=Count('order'),
        station_revenue=Sum('order__total_amount')
    ).filter(order_count__gt=0).order_by('-order_count')[:5]
    if top_stations:
        top_station_max = top_stations.first().order_count
    else:
        top_station_max = 1

    top_drivers = Driver.objects.filter(
        order__isnull=False
    ).annotate(
        delivery_count=Count('order')
    ).order_by('-delivery_count')[:5]
    if top_drivers:
        top_driver_max = top_drivers.first().delivery_count
    else:
        top_driver_max = 1

    ctx.update({
        "period_orders": period_orders,
        "period_litres": period_litres,
        "period_revenue": int(period_revenue),
        "new_users": new_users,
        "report_week": report_week,
        "report_max": report_max,
        "fuel_data": fuel_data,
        "top_stations": top_stations,
        "top_station_max": top_station_max,
        "top_drivers": top_drivers,
        "top_driver_max": top_driver_max,
    })
    return render(request, 'admin_panel/reports.html', ctx)


# ===========================
#  ADMIN MISC
# ===========================

def admin_demand(request):
    ctx = get_admin_base_context(request)
    return render(request, 'admin_panel/reports.html', ctx)


@login_required(login_url='login')
@role_required('admin')
def admin_activity(request):
    ctx = get_admin_base_context(request)
    today = timezone.now().date()

    recent_notifications = Notification.objects.select_related('user').order_by('-created_at')[:10]
    active_sessions = User.objects.filter(last_login__date=today).count()
    orders_today = Order.objects.filter(created_at__date=today).count()
    on_duty_drivers = Driver.objects.filter(on_duty=True).count()
    live_deliveries = Order.objects.filter(
        status__in=["confirmed", "assigned", "picked_up", "delivering"]
    ).count()

    ctx.update({
        "recent_notifications": recent_notifications,
        "active_sessions": active_sessions,
        "orders_today": orders_today,
        "on_duty_drivers": on_duty_drivers,
        "live_deliveries": live_deliveries,
    })
    return render(request, 'admin_panel/activity.html', ctx)


@login_required(login_url='login')
@role_required('admin')
def admin_settings(request):
    ctx = get_admin_base_context(request)
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
    ctx = get_admin_base_context(request)
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