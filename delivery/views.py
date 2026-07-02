from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.utils.timesince import timesince
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
import json

from accounts.decorators import role_required
from accounts.models import Driver
from orders.models import Order
from delivery.models import DeliveryLog
from core.models import Notification


def get_base_context(request):
    driver = request.user.driver
    active_order = Order.objects.filter(
        driver=driver,
        status__in=["assigned", "picked_up", "delivering"]
    ).select_related("station", "customer").first()
    new_orders_count = Order.objects.filter(driver=driver, status="assigned").count()
    notif_count = Notification.objects.filter(user=request.user, is_read=False).count()

    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")[:5]
    notifs_list = []
    for n in notifications:
        notifs_list.append({
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "time": timesince(n.created_at) + " ago",
        })
    notifs_json = json.dumps(notifs_list)

    return {
        "driver": driver,
        "active_order": active_order,
        "new_orders_count": new_orders_count,
        "notif_count": notif_count,
        "notifs_json": notifs_json,
    }


@login_required(login_url="login")
@role_required("driver")
def driver_home(request):
    ctx = get_base_context(request)
    driver = ctx["driver"]
    today = timezone.now().date()

    today_deliveries = DeliveryLog.objects.filter(
        driver=driver, created_at__date=today
    ).count()

    total_deliveries = DeliveryLog.objects.filter(driver=driver).count()

    today_earnings = DeliveryLog.objects.filter(
        driver=driver, created_at__date=today
    ).aggregate(total=Sum("driver_earning"))["total"] or 0

    week_start = today - timezone.timedelta(days=today.weekday())
    weekly_earnings = DeliveryLog.objects.filter(
        driver=driver, created_at__date__gte=week_start
    ).aggregate(total=Sum("driver_earning"))["total"] or 0

    assigned_orders = Order.objects.filter(
        driver=driver, status="assigned"
    ).select_related("station", "customer").order_by("-driver_assigned_at")

    recent_deliveries = DeliveryLog.objects.filter(
        driver=driver
    ).select_related("order", "order__customer").order_by("-completed_at")[:5]

    now = timezone.now()
    if now.hour < 12:
        time_of_day = "Morning"
    elif now.hour < 18:
        time_of_day = "Afternoon"
    else:
        time_of_day = "Evening"

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    earnings_by_day_list = []
    for i in range(7):
        day = week_start + timezone.timedelta(days=i)
        total = DeliveryLog.objects.filter(driver=driver, created_at__date=day).aggregate(total=Sum('driver_earning'))['total'] or 0
        earnings_by_day_list.append(int(total))
    max_val = max(earnings_by_day_list) if any(earnings_by_day_list) else 1
    earnings_data = []
    for i, amt in enumerate(earnings_by_day_list):
        earnings_data.append({
            'day': day_names[i],
            'amount': amt,
            'pct': round(amt / max_val * 100),
        })

    # On-time rate for performance section
    today_deliveries_total = DeliveryLog.objects.filter(driver=driver, created_at__date=today).count()
    on_time_today = DeliveryLog.objects.filter(driver=driver, created_at__date=today, status="delivered").count()
    on_time_pct = round((on_time_today / today_deliveries_total * 100)) if today_deliveries_total > 0 else 100

    ctx.update({
        "time_of_day": time_of_day,
        "today_deliveries": today_deliveries,
        "total_deliveries": total_deliveries,
        "rating": driver.rating,
        "today_earnings": int(today_earnings),
        "weekly_earnings": int(weekly_earnings),
        "assigned_orders": assigned_orders,
        "recent_deliveries": recent_deliveries,
        "earnings_data": earnings_data,
        "on_time_pct": on_time_pct,
    })

    return render(request, "driver/home.html", ctx)


@login_required(login_url="login")
@role_required("driver")
def driver_orders(request):
    ctx = get_base_context(request)
    driver = ctx["driver"]

    assigned_orders = Order.objects.filter(
        driver=driver,
        status__in=["assigned", "picked_up", "delivering"]
    ).select_related("station", "customer").order_by("-driver_assigned_at")

    ctx["assigned_orders"] = assigned_orders
    return render(request, "driver/orders.html", ctx)


@login_required(login_url="login")
@role_required("driver")
def driver_active(request):
    ctx = get_base_context(request)
    driver = ctx["driver"]

    active_order = Order.objects.filter(
        driver=driver,
        status__in=["assigned", "picked_up", "delivering"]
    ).select_related("station", "customer").first()

    ctx["active_order"] = active_order
    return render(request, "driver/active.html", ctx)


@login_required(login_url="login")
@role_required("driver")
def driver_earnings(request):
    ctx = get_base_context(request)
    driver = ctx["driver"]
    today = timezone.now().date()
    week_start = today - timezone.timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    today_earnings = DeliveryLog.objects.filter(
        driver=driver, created_at__date=today
    ).aggregate(total=Sum("driver_earning"))["total"] or 0

    weekly_earnings = DeliveryLog.objects.filter(
        driver=driver, created_at__date__gte=week_start
    ).aggregate(total=Sum("driver_earning"))["total"] or 0

    monthly_earnings = DeliveryLog.objects.filter(
        driver=driver, created_at__date__gte=month_start
    ).aggregate(total=Sum("driver_earning"))["total"] or 0

    total_deliveries = DeliveryLog.objects.filter(driver=driver).count()

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    earnings_by_day_list = []
    for i in range(7):
        day = week_start + timezone.timedelta(days=i)
        total = DeliveryLog.objects.filter(driver=driver, created_at__date=day).aggregate(total=Sum('driver_earning'))['total'] or 0
        earnings_by_day_list.append(int(total))
    max_val = max(earnings_by_day_list) if any(earnings_by_day_list) else 1
    earnings_data = []
    for i, amt in enumerate(earnings_by_day_list):
        earnings_data.append({
            'day': day_names[i],
            'amount': amt,
            'pct': round(amt / max_val * 100),
        })

    ctx.update({
        "today_earnings": int(today_earnings),
        "weekly_earnings": int(weekly_earnings),
        "monthly_earnings": int(monthly_earnings),
        "total_deliveries": total_deliveries,
        "earnings_data": earnings_data,
    })
    return render(request, "driver/earnings.html", ctx)


@login_required(login_url="login")
@role_required("driver")
def driver_history(request):
    ctx = get_base_context(request)
    driver = ctx["driver"]

    deliveries = DeliveryLog.objects.filter(
        driver=driver
    ).select_related("order", "order__customer").order_by("-completed_at")

    ctx["deliveries"] = deliveries
    return render(request, "driver/history.html", ctx)


@login_required(login_url="login")
@role_required("driver")
def driver_profile(request):
    ctx = get_base_context(request)
    driver = ctx["driver"]

    total_deliveries = DeliveryLog.objects.filter(driver=driver).count()
    on_time_count = DeliveryLog.objects.filter(
        driver=driver, status="delivered"
    ).count()
    on_time_pct = round((on_time_count / total_deliveries * 100)) if total_deliveries > 0 else 0

    ctx.update({
        "total_deliveries": total_deliveries,
        "rating": driver.rating,
        "on_time_pct": on_time_pct,
    })
    return render(request, "driver/profile.html", ctx)


@login_required(login_url="login")
@role_required("driver")
def driver_notifications(request):
    ctx = get_base_context(request)
    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()
    ctx["notifications"] = notifications
    ctx["unread_count"] = unread_count
    return render(request, "driver/notifications.html", ctx)


@login_required(login_url="login")
@role_required("driver")
def driver_update_profile(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.save()

        driver = user.driver
        driver.phone = request.POST.get("phone", driver.phone)
        driver.plate_number = request.POST.get("plate_number", driver.plate_number)
        driver.save()

        messages.success(request, "Profile updated successfully")

    return redirect("driver_profile")


@login_required(login_url="login")
@role_required("driver")
def driver_change_password(request):
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

    return redirect("driver_profile")


@login_required(login_url="login")
@role_required("driver")
def driver_update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, driver=request.user.driver)

    if request.method == "POST":
        new_status = request.POST.get("status")

        valid_transitions = {
            "assigned": "picked_up",
            "picked_up": "delivering",
            "delivering": "delivered",
        }

        expected = valid_transitions.get(order.status)
        if new_status == expected:
            order.status = new_status
            if new_status == "picked_up":
                order.picked_up_at = timezone.now()
            elif new_status == "delivered":
                order.delivered_at = timezone.now()
            order.save()

            if new_status == "delivered":
                delivery_log, created = DeliveryLog.objects.get_or_create(
                    order=order,
                    driver=request.user.driver,
                    defaults={"status": "delivered", "completed_at": timezone.now()},
                )
                if not created:
                    delivery_log.status = "delivered"
                    delivery_log.completed_at = timezone.now()
                    delivery_log.save()

                Notification.objects.create(
                    user=order.customer,
                    title="Fuel Delivered",
                    message=f"Your fuel order #{order.id} has been delivered successfully.",
                )

    return redirect("driver_active")


@login_required(login_url="login")
@role_required("driver")
def driver_report_issue(request, order_id):
    if request.method == "POST":
        issue_type = request.POST.get("issue_type", "other")
        description = request.POST.get("description", "")
        messages.success(request, "Issue reported. We'll look into it shortly.")
    return redirect("driver_active")


@login_required(login_url="login")
@role_required("driver")
def driver_update_location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lat = data.get("lat")
            lng = data.get("lng")
            return JsonResponse({"success": True})
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({"success": False}, status=400)
    return JsonResponse({"success": False}, status=405)


@login_required
def driver_toggle_duty(request):
    if request.method == "POST":
        driver = request.user.driver
        driver.on_duty = not driver.on_duty
        driver.save()
        return JsonResponse({"on_duty": driver.on_duty})
    return JsonResponse({"error": "POST only"}, status=405)
