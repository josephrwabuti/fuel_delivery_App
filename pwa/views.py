import json
from datetime import timedelta

from functools import wraps

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db.models import Sum, Count, Avg, F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.timesince import timesince
from django.views.decorators.csrf import csrf_exempt

from accounts.decorators import role_required
from accounts.models import User, Station, Driver, FuelPrice
from providers.models import StationStock
from core.models import Notification
from delivery.models import DeliveryLog
from orders.models import Order


def api_login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Authentication required"}, status=401)
        return view(request, *args, **kwargs)
    return wrapper


def pwa_index(request):
    return render(request, "pwa/index.html")


def csrf_token(request):
    from django.middleware.csrf import get_token
    return JsonResponse({"csrfToken": get_token(request)})


# ===========================
#  AUTH
# ===========================

@csrf_exempt
def api_login(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
        email = data.get("email", "")
        password = data.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({
                "status": "success",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "phone": user.phone,
                }
            })
        return JsonResponse({"status": "error", "message": "Invalid email or password"}, status=401)
    return JsonResponse({"status": "error", "message": "POST required"}, status=405)


@csrf_exempt
def api_register(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        email = data.get("email", "")
        password = data.get("password", "")
        role = data.get("role", "customer")
        phone = data.get("phone", "")

        if User.objects.filter(username=email).exists():
            return JsonResponse({"status": "error", "message": "User already exists"}, status=400)
        if not email or not password:
            return JsonResponse({"status": "error", "message": "Email and password are required"}, status=400)

        user = User.objects.create_user(
            username=email, email=email, password=password,
            first_name=first_name, last_name=last_name,
            role=role, phone=phone,
        )
        if role == "driver":
            Driver.objects.create(
                user=user, name=f"{first_name} {last_name}",
                phone=phone, status="pending", is_approved=False,
                licence_number=data.get("licence_number", ""),
                vehicle_type=data.get("vehicle_type", ""),
                plate_number=data.get("plate_number", ""),
            )
        if role == "provider":
            Station.objects.create(
                owner=user, name=data.get("station_name", f"{first_name} Station"),
                address=data.get("station_address", ""),
                lat=float(data.get("lat", 0)), lng=float(data.get("lng", 0)),
                phone=phone, status="pending",
            )
        return JsonResponse({"status": "success", "message": "Account created successfully"})
    return JsonResponse({"status": "error", "message": "POST required"}, status=405)


def api_logout(request):
    logout(request)
    return JsonResponse({"status": "success"})


def api_user(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Not authenticated"}, status=401)
    user_data = {
        "id": request.user.id,
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "role": request.user.role,
        "phone": request.user.phone,
    }
    if request.user.role == "driver":
        try:
            driver = request.user.driver
            user_data["driver"] = {
                "id": driver.id,
                "name": driver.name,
                "phone": driver.phone,
                "plate": driver.plate,
                "rating": float(driver.rating),
                "on_duty": driver.on_duty,
                "status": driver.status,
                "is_approved": driver.is_approved,
                "licence_number": driver.licence_number,
                "plate_number": driver.plate_number,
                "vehicle_type": driver.vehicle_type,
                "station_id": driver.station_id,
                "station_name": driver.station.name if driver.station else None,
            }
        except Driver.DoesNotExist:
            pass
    return JsonResponse({"status": "success", "user": user_data})


# ===========================
#  CUSTOMER API
# ===========================

@api_login_required
@role_required("customer")
def api_customer_dashboard(request):
    user = request.user
    nearby_stations = Station.objects.filter(
        status="approved", is_open=True
    ).prefetch_related("fuels").order_by("-created_at")[:6]

    recent_orders = Order.objects.filter(customer=user).select_related("station").order_by("-created_at")[:5]

    active_order = Order.objects.filter(
        customer=user, status__in=["pending", "confirmed", "assigned", "out"]
    ).select_related("driver", "station").first()

    total_orders = Order.objects.filter(customer=user).count()
    delivered_orders = Order.objects.filter(customer=user, status="delivered").count()
    total_litres = Order.objects.filter(customer=user).aggregate(total=Sum("quantity"))["total"] or 0

    today = timezone.now()
    hour = today.hour
    if hour < 12:
        time_of_day = "Morning"
    elif hour < 17:
        time_of_day = "Afternoon"
    else:
        time_of_day = "Evening"

    delivered_qs = Order.objects.filter(customer=user, status="delivered")
    avg_seconds = delivered_qs.exclude(confirmed_at=None).annotate(
        diff=F("delivered_at") - F("confirmed_at")
    ).aggregate(avg=Avg("diff"))["avg"]
    avg_delivery_time = int(avg_seconds.total_seconds() / 60) if avg_seconds else None

    return JsonResponse({
        "status": "success",
        "time_of_day": time_of_day,
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "total_litres": total_litres,
        "avg_delivery_time": avg_delivery_time,
        "nearby_stations": [{
            "id": s.id, "name": s.name, "address": s.address,
            "lat": s.lat, "lng": s.lng, "rating": float(s.rating),
            "review_count": s.review_count, "is_open": s.is_open,
            "hours": s.hours or "24/7", "phone": s.phone or "—",
            "delivery_radius": s.delivery_radius,
        } for s in nearby_stations],
        "recent_orders": [{
            "id": o.id, "display_id": o.display_id, "customer_seq": o.customer_seq, "station_name": o.station.name if o.station else "—",
            "fuel_type": o.fuel_type, "quantity": o.quantity,
            "total_amount": float(o.total_amount),
            "status": o.status, "status_display": o.get_status_display(),
            "created_at": o.created_at.strftime("%d %b %Y"),
        } for o in recent_orders],
        "active_order": None if not active_order else {
            "id": active_order.id, "display_id": active_order.display_id, "customer_seq": active_order.customer_seq,
            "station_name": active_order.station.name if active_order.station else "—",
            "fuel_type": active_order.fuel_type,
            "quantity": active_order.quantity,
            "total_amount": float(active_order.total_amount),
            "status": active_order.status,
            "status_display": active_order.get_status_display(),
            "driver_name": active_order.driver.name if active_order.driver else None,
            "driver_phone": active_order.driver.phone if active_order.driver else None,
            "driver_rating": float(active_order.driver.rating) if active_order.driver else None,
            "driver_plate": active_order.driver.plate if active_order.driver else None,
        },
    })


@api_login_required
@role_required("customer")
def api_stations(request):
    stations = Station.objects.filter(status="approved", is_open=True).prefetch_related("fuels")
    return JsonResponse({
        "status": "success",
        "stations": [{
            "id": s.id, "name": s.name, "address": s.address,
            "lat": s.lat, "lng": s.lng, "rating": float(s.rating),
            "review_count": s.review_count, "is_open": s.is_open,
            "hours": s.hours or "24/7", "phone": s.phone or "—",
            "delivery_radius": s.delivery_radius,
            "description": s.description or "",
            "fuels": [{"type": f.type, "price": float(f.price), "available": f.available} for f in s.fuels.all()],
        } for s in stations],
    })


@api_login_required
def api_create_order(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    station_id = data.get("station_id")
    fuel_type = data.get("fuel_type")
    quantity = data.get("quantity")
    delivery_address = data.get("delivery_address", "")
    phone = data.get("phone", "")
    notes = data.get("notes", "")
    payment_method = data.get("payment_method", "Cash")
    customer_lat = data.get("lat")
    customer_lng = data.get("lng")
    landmark = data.get("landmark", "")

    if not all([station_id, fuel_type, quantity]):
        return JsonResponse({"status": "error", "message": "station_id, fuel_type, quantity required"}, status=400)

    station = get_object_or_404(Station, id=station_id)
    if not station.is_open:
        return JsonResponse({"status": "error", "message": "Station is currently closed"}, status=400)

    try:
        fuel_price = station.fuels.get(type=fuel_type)
        price_per_litre = float(fuel_price.price)
    except FuelPrice.DoesNotExist:
        stock = StationStock.objects.filter(station=station, fuel_type=fuel_type).first()
        price_per_litre = float(stock.price_per_litre) if stock else {"Petrol": 2850, "Diesel": 2700, "Kerosene": 2600}.get(fuel_type, 2850)

    total_price = price_per_litre * float(quantity) + 2000

    stock = StationStock.objects.filter(station=station, fuel_type=fuel_type).first()
    if stock and stock.litres_available >= float(quantity):
        stock.litres_available -= float(quantity)
        stock.save()

    last_seq = Order.objects.filter(customer=request.user).order_by("-customer_seq").first()
    next_seq = (last_seq.customer_seq + 1) if last_seq else 1

    order = Order.objects.create(
        customer=request.user, station=station,
        fuel_type=fuel_type, quantity=quantity,
        total_amount=total_price, status="pending",
        delivery_address=delivery_address, phone=phone,
        notes=notes, payment_method=payment_method,
        customer_lat=customer_lat, customer_lng=customer_lng,
        landmark=landmark, customer_seq=next_seq,
    )
    return JsonResponse({"status": "success", "order_id": order.id, "display_id": order.display_id, "customer_seq": order.customer_seq, "total_amount": float(total_price)})


@api_login_required
def api_tracking(request):
    active_order = Order.objects.filter(
        customer=request.user
    ).exclude(status="delivered").exclude(status="cancelled").select_related("station", "driver").first()
    if not active_order:
        return JsonResponse({"status": "success", "active_order": None})
    return JsonResponse({
        "status": "success",
        "active_order": {
            "id": active_order.id, "display_id": active_order.display_id, "customer_seq": active_order.customer_seq,
            "station_name": active_order.station.name if active_order.station else "—",
            "station_address": active_order.station.address if active_order.station else "",
            "station_phone": active_order.station.phone if active_order.station else "",
            "fuel_type": active_order.fuel_type,
            "quantity": active_order.quantity,
            "total_amount": float(active_order.total_amount),
            "status": active_order.status,
            "status_display": active_order.get_status_display(),
            "delivery_address": active_order.delivery_address or "",
            "payment_method": active_order.payment_method or "—",
            "phone": active_order.phone or "",
            "notes": active_order.notes or "",
            "landmark": active_order.landmark or "",
            "created_at": active_order.created_at.strftime("%d %b %Y, %H:%M"),
            "confirmed_at": active_order.confirmed_at.strftime("%H:%M") if active_order.confirmed_at else None,
            "picked_up_at": active_order.picked_up_at.strftime("%H:%M") if active_order.picked_up_at else None,
            "driver": None if not active_order.driver else {
                "name": active_order.driver.name,
                "phone": active_order.driver.phone,
                "rating": float(active_order.driver.rating),
                "plate": active_order.driver.plate or active_order.driver.plate_number or "",
                "vehicle_type": active_order.driver.vehicle_type or "",
                "current_lat": active_order.driver.current_lat,
                "current_lng": active_order.driver.current_lng,
                "location_updated_at": active_order.driver.location_updated_at.strftime("%H:%M") if active_order.driver.location_updated_at else None,
            },
        },
    })


@api_login_required
def api_history(request):
    orders = Order.objects.filter(customer=request.user).select_related("station", "driver").order_by("-created_at")
    return JsonResponse({
        "status": "success",
        "orders": [{
            "id": o.id, "display_id": o.display_id, "customer_seq": o.customer_seq,
            "station_name": o.station.name if o.station else "—",
            "fuel_type": o.fuel_type,
            "quantity": o.quantity,
            "total_amount": float(o.total_amount),
            "status": o.status,
            "status_display": o.get_status_display(),
            "delivery_address": o.delivery_address or "—",
            "driver_name": o.driver.name if o.driver else "—",
            "payment_method": o.payment_method or "—",
            "created_at": o.created_at.strftime("%d %b %Y"),
            "delivered_at": o.delivered_at.strftime("%d %b %Y, %H:%M") if o.delivered_at else None,
        } for o in orders],
    })


@api_login_required
def api_cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if order.status in ["delivered", "cancelled"]:
        return JsonResponse({"status": "error", "message": "Order cannot be cancelled"}, status=400)
    order.status = "cancelled"
    order.save()
    return JsonResponse({"status": "success"})


@api_login_required
def api_confirm_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if order.status == "delivered":
        return JsonResponse({"status": "error", "message": "Already delivered"}, status=400)
    order.status = "delivered"
    order.delivered_at = timezone.now()
    order.save()
    return JsonResponse({"status": "success"})


@api_login_required
@role_required("customer")
def api_customer_profile(request):
    user = request.user
    total_orders = Order.objects.filter(customer=user).count()
    delivered_orders = Order.objects.filter(customer=user, status="delivered").count()
    total_litres = Order.objects.filter(customer=user).aggregate(total=Sum("quantity"))["total"] or 0
    return JsonResponse({
        "status": "success",
        "profile": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "date_joined": user.date_joined.strftime("%d %b %Y"),
        },
        "stats": {
            "total_orders": total_orders,
            "delivered_orders": delivered_orders,
            "total_litres": total_litres,
        },
    })


@api_login_required
@role_required("customer")
def api_customer_update_profile(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    user = request.user
    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user.phone = data.get("phone", user.phone)
    user.save()
    return JsonResponse({"status": "success", "message": "Profile updated"})


@api_login_required
def api_customer_change_password(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    user = request.user
    old = data.get("old_password", "")
    p1 = data.get("password1", "")
    p2 = data.get("password2", "")
    if not user.check_password(old):
        return JsonResponse({"status": "error", "message": "Current password is incorrect"}, status=400)
    if p1 != p2:
        return JsonResponse({"status": "error", "message": "New passwords do not match"}, status=400)
    if len(p1) < 8:
        return JsonResponse({"status": "error", "message": "Password must be at least 8 characters"}, status=400)
    user.set_password(p1)
    user.save()
    update_session_auth_hash(request, user)
    return JsonResponse({"status": "success", "message": "Password changed"})


@api_login_required
def api_customer_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return JsonResponse({
        "status": "success",
        "unread_count": notifications.filter(is_read=False).count(),
        "notifications": [{
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "time": timesince(n.created_at) + " ago",
        } for n in notifications],
    })


# ===========================
#  DRIVER API
# ===========================

def get_driver_context(user):
    try:
        driver = user.driver
    except Driver.DoesNotExist:
        return None
    active_order = Order.objects.filter(
        driver=driver, status__in=["assigned", "picked_up", "delivering"]
    ).select_related("station", "customer").first()
    new_orders_count = Order.objects.filter(driver=driver, status="assigned").count()
    notif_count = Notification.objects.filter(user=user, is_read=False).count()
    return {"driver": driver, "active_order": active_order, "new_orders_count": new_orders_count, "notif_count": notif_count}


@api_login_required
@role_required("driver")
def api_driver_dashboard(request):
    ctx = get_driver_context(request.user)
    if not ctx:
        return JsonResponse({"status": "error", "message": "Driver profile not found"}, status=404)
    driver = ctx["driver"]
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    today_deliveries = DeliveryLog.objects.filter(driver=driver, created_at__date=today).count()
    total_deliveries = DeliveryLog.objects.filter(driver=driver).count()
    today_earnings = DeliveryLog.objects.filter(driver=driver, created_at__date=today).aggregate(total=Sum("driver_earning"))["total"] or 0
    weekly_earnings = DeliveryLog.objects.filter(driver=driver, created_at__date__gte=week_start).aggregate(total=Sum("driver_earning"))["total"] or 0

    assigned_orders = Order.objects.filter(driver=driver, status="assigned").select_related("station", "customer").order_by("-driver_assigned_at")
    recent_deliveries = DeliveryLog.objects.filter(driver=driver).select_related("order", "order__customer").order_by("-completed_at")[:5]

    now = timezone.now()
    time_of_day = "Morning" if now.hour < 12 else ("Afternoon" if now.hour < 18 else "Evening")

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    earnings_by_day = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        total = DeliveryLog.objects.filter(driver=driver, created_at__date=day).aggregate(total=Sum("driver_earning"))["total"] or 0
        earnings_by_day.append(int(total))
    max_val = max(earnings_by_day) if any(earnings_by_day) else 1

    today_deliveries_total = DeliveryLog.objects.filter(driver=driver, created_at__date=today).count()
    on_time_today = DeliveryLog.objects.filter(driver=driver, created_at__date=today, status="delivered").count()
    on_time_pct = round((on_time_today / today_deliveries_total * 100)) if today_deliveries_total > 0 else 100

    return JsonResponse({
        "status": "success",
        "time_of_day": time_of_day,
        "today_deliveries": today_deliveries,
        "total_deliveries": total_deliveries,
        "rating": float(driver.rating),
        "today_earnings": int(today_earnings),
        "weekly_earnings": int(weekly_earnings),
        "on_duty": driver.on_duty,
        "on_time_pct": on_time_pct,
        "earnings_data": [{"day": day_names[i], "amount": amt, "pct": round(amt / max_val * 100)} for i, amt in enumerate(earnings_by_day)],
        "assigned_orders": [{
            "id": o.id,
            "station_name": o.station.name if o.station else "—",
            "customer_name": o.customer.get_full_name() or o.customer.email,
            "customer_phone": o.customer.phone or "",
            "fuel_type": o.fuel_type,
            "quantity": o.quantity,
            "delivery_address": o.delivery_address or "",
            "total_amount": float(o.total_amount),
            "assigned_at": o.driver_assigned_at.strftime("%H:%M") if o.driver_assigned_at else "",
            "created_at": o.created_at.strftime("%d %b %Y, %H:%M"),
            "customer_lat": float(o.customer_lat) if o.customer_lat else None,
            "customer_lng": float(o.customer_lng) if o.customer_lng else None,
        } for o in assigned_orders],
        "recent_deliveries": [{
            "id": d.order_id,
            "customer_name": d.order.customer.get_full_name() or d.order.customer.email if d.order else "—",
            "fuel_type": d.order.fuel_type if d.order else "—",
            "quantity": d.order.quantity if d.order else 0,
            "driver_earning": int(d.driver_earning) if d.driver_earning else 0,
            "completed_at": d.completed_at.strftime("%d %b %Y") if d.completed_at else "—",
        } for d in recent_deliveries],
    })


@api_login_required
@role_required("driver")
def api_driver_orders(request):
    ctx = get_driver_context(request.user)
    if not ctx:
        return JsonResponse({"status": "error", "message": "Driver profile not found"}, status=404)
    driver = ctx["driver"]
    assigned_orders = Order.objects.filter(
        driver=driver, status__in=["assigned", "picked_up", "delivering"]
    ).select_related("station", "customer").order_by("-driver_assigned_at")
    return JsonResponse({
        "status": "success",
        "orders": [{
            "id": o.id,
            "station_name": o.station.name if o.station else "—",
            "station_address": o.station.address if o.station else "",
            "customer_name": o.customer.get_full_name() or o.customer.email,
            "customer_phone": o.customer.phone or "",
            "fuel_type": o.fuel_type,
            "quantity": o.quantity,
            "delivery_address": o.delivery_address or "",
            "total_amount": float(o.total_amount),
            "status": o.status,
            "status_display": o.get_status_display(),
            "customer_lat": float(o.customer_lat) if o.customer_lat else None,
            "customer_lng": float(o.customer_lng) if o.customer_lng else None,
            "assigned_at": o.driver_assigned_at.strftime("%H:%M") if o.driver_assigned_at else "",
            "created_at": o.created_at.strftime("%d %b %Y, %H:%M"),
            "phone": o.phone or "",
            "notes": o.notes or "",
            "landmark": o.landmark or "",
            "payment_method": o.payment_method or "—",
        } for o in assigned_orders],
    })


@api_login_required
@role_required("driver")
def api_driver_active(request):
    ctx = get_driver_context(request.user)
    if not ctx:
        return JsonResponse({"status": "error", "message": "Driver profile not found"}, status=404)
    active_order = ctx["active_order"]
    if not active_order:
        return JsonResponse({"status": "success", "active_order": None})
    return JsonResponse({
        "status": "success",
        "active_order": {
            "id": active_order.id,
            "station_name": active_order.station.name if active_order.station else "—",
            "station_address": active_order.station.address if active_order.station else "",
            "station_lat": float(active_order.station.lat) if active_order.station else None,
            "station_lng": float(active_order.station.lng) if active_order.station else None,
            "customer_name": active_order.customer.get_full_name() or active_order.customer.email,
            "customer_phone": active_order.customer.phone or "",
            "fuel_type": active_order.fuel_type,
            "quantity": active_order.quantity,
            "delivery_address": active_order.delivery_address or "",
            "total_amount": float(active_order.total_amount),
            "status": active_order.status,
            "status_display": active_order.get_status_display(),
            "customer_lat": float(active_order.customer_lat) if active_order.customer_lat else None,
            "customer_lng": float(active_order.customer_lng) if active_order.customer_lng else None,
            "phone": active_order.phone or "",
            "notes": active_order.notes or "",
            "landmark": active_order.landmark or "",
            "payment_method": active_order.payment_method or "—",
            "created_at": active_order.created_at.strftime("%d %b %Y, %H:%M"),
            "confirmed_at": active_order.confirmed_at.strftime("%H:%M") if active_order.confirmed_at else None,
            "picked_up_at": active_order.picked_up_at.strftime("%H:%M") if active_order.picked_up_at else None,
        },
    })


@api_login_required
@role_required("driver")
def api_driver_update_status(request, order_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    order = get_object_or_404(Order, id=order_id, driver=request.user.driver)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    new_status = data.get("status")
    valid_transitions = {
        "assigned": "picked_up",
        "picked_up": "delivering",
        "delivering": "delivered",
    }
    expected = valid_transitions.get(order.status)
    if new_status != expected:
        return JsonResponse({"status": "error", "message": f"Invalid transition from {order.status} to {new_status}"}, status=400)

    order.status = new_status
    if new_status == "picked_up":
        order.picked_up_at = timezone.now()
    elif new_status == "delivered":
        order.delivered_at = timezone.now()
    order.save()

    if new_status == "delivered":
        dl, created = DeliveryLog.objects.get_or_create(
            order=order, driver=request.user.driver,
            defaults={"status": "delivered", "completed_at": timezone.now(), "driver_earning": float(order.total_amount) * 0.1},
        )
        if not created:
            dl.status = "delivered"
            dl.completed_at = timezone.now()
            dl.driver_earning = float(order.total_amount) * 0.1
            dl.save()
        Notification.objects.create(
            user=order.customer,
            title="Fuel Delivered",
            message=f"Your fuel order #{order.display_id} has been delivered successfully.",
        )

    return JsonResponse({"status": "success", "new_status": new_status})


@api_login_required
@role_required("driver")
def api_driver_update_location(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
        lat = data.get("lat")
        lng = data.get("lng")
        if lat is None or lng is None:
            return JsonResponse({"status": "error", "message": "lat and lng required"}, status=400)
        driver = request.user.driver
        driver.current_lat = float(lat)
        driver.current_lng = float(lng)
        driver.location_updated_at = timezone.now()
        driver.save(update_fields=["current_lat", "current_lng", "location_updated_at"])
        return JsonResponse({"status": "success"})
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"status": "error", "message": "Invalid data"}, status=400)


@api_login_required
@role_required("driver")
def api_driver_toggle_duty(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    driver = request.user.driver
    driver.on_duty = not driver.on_duty
    driver.save()
    return JsonResponse({"status": "success", "on_duty": driver.on_duty})


@api_login_required
@role_required("driver")
def api_driver_earnings(request):
    ctx = get_driver_context(request.user)
    if not ctx:
        return JsonResponse({"status": "error", "message": "Driver profile not found"}, status=404)
    driver = ctx["driver"]
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    today_earnings = DeliveryLog.objects.filter(driver=driver, created_at__date=today).aggregate(total=Sum("driver_earning"))["total"] or 0
    weekly_earnings = DeliveryLog.objects.filter(driver=driver, created_at__date__gte=week_start).aggregate(total=Sum("driver_earning"))["total"] or 0
    monthly_earnings = DeliveryLog.objects.filter(driver=driver, created_at__date__gte=month_start).aggregate(total=Sum("driver_earning"))["total"] or 0
    total_deliveries = DeliveryLog.objects.filter(driver=driver).count()

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    earnings_by_day = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        total = DeliveryLog.objects.filter(driver=driver, created_at__date=day).aggregate(total=Sum("driver_earning"))["total"] or 0
        earnings_by_day.append(int(total))
    max_val = max(earnings_by_day) if any(earnings_by_day) else 1

    return JsonResponse({
        "status": "success",
        "today_earnings": int(today_earnings),
        "weekly_earnings": int(weekly_earnings),
        "monthly_earnings": int(monthly_earnings),
        "total_deliveries": total_deliveries,
        "earnings_data": [{"day": day_names[i], "amount": amt, "pct": round(amt / max_val * 100)} for i, amt in enumerate(earnings_by_day)],
    })


@api_login_required
@role_required("driver")
def api_driver_history(request):
    ctx = get_driver_context(request.user)
    if not ctx:
        return JsonResponse({"status": "error", "message": "Driver profile not found"}, status=404)
    driver = ctx["driver"]
    deliveries = DeliveryLog.objects.filter(driver=driver).select_related("order", "order__customer").order_by("-completed_at")
    return JsonResponse({
        "status": "success",
        "deliveries": [{
            "id": d.order_id,
            "customer_name": d.order.customer.get_full_name() or d.order.customer.email if d.order else "—",
            "fuel_type": d.order.fuel_type if d.order else "—",
            "quantity": d.order.quantity if d.order else 0,
            "delivery_address": d.order.delivery_address if d.order else "",
            "driver_earning": int(d.driver_earning) if d.driver_earning else 0,
            "status": d.status,
            "completed_at": d.completed_at.strftime("%d %b %Y, %H:%M") if d.completed_at else "—",
            "created_at": d.created_at.strftime("%d %b %Y") if d.created_at else "—",
        } for d in deliveries],
    })


@api_login_required
@role_required("driver")
def api_driver_profile(request):
    ctx = get_driver_context(request.user)
    if not ctx:
        return JsonResponse({"status": "error", "message": "Driver profile not found"}, status=404)
    driver = ctx["driver"]
    user = request.user
    total_deliveries = DeliveryLog.objects.filter(driver=driver).count()
    on_time_count = DeliveryLog.objects.filter(driver=driver, status="delivered").count()
    on_time_pct = round((on_time_count / total_deliveries * 100)) if total_deliveries > 0 else 0

    return JsonResponse({
        "status": "success",
        "profile": {
            "name": driver.name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": driver.phone or user.phone,
            "licence_number": driver.licence_number or "",
            "plate_number": driver.plate_number or driver.plate or "",
            "vehicle_type": driver.vehicle_type or "",
            "rating": float(driver.rating),
            "on_duty": driver.on_duty,
            "status": driver.status,
            "station_name": driver.station.name if driver.station else None,
            "date_joined": user.date_joined.strftime("%d %b %Y"),
        },
        "stats": {
            "total_deliveries": total_deliveries,
            "on_time_pct": on_time_pct,
        },
    })


@api_login_required
@role_required("driver")
def api_driver_update_profile(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    user = request.user
    driver = user.driver
    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user.email = data.get("email", user.email)
    user.save()
    driver.phone = data.get("phone", driver.phone)
    driver.plate_number = data.get("plate_number", driver.plate_number or driver.plate)
    driver.save()
    return JsonResponse({"status": "success", "message": "Profile updated"})


@api_login_required
@role_required("driver")
def api_driver_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return JsonResponse({
        "status": "success",
        "unread_count": notifications.filter(is_read=False).count(),
        "notifications": [{
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "time": timesince(n.created_at) + " ago",
        } for n in notifications],
    })


@api_login_required
def api_dismiss_notification(request, notif_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    Notification.objects.filter(id=notif_id, user=request.user).delete()
    return JsonResponse({"status": "success"})


@api_login_required
def api_mark_notifications_read(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"status": "success"})
