from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F, Value, Case, When, CharField
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from accounts.decorators import role_required
from accounts.models import Station, Driver
from orders.models import Order
from providers.models import StationStock
from delivery.models import DeliveryLog
from core.models import Notification
import json
from datetime import timedelta, date, datetime


def map_status_tag(qs):
    return qs.annotate(
        display_status=Case(
            When(status='out', then=Value('delivering')),
            default=F('status'),
            output_field=CharField(),
        )
    )


def get_context_base(request):
    station = request.user.station
    pending_count = Order.objects.filter(station=station, status='pending').count()
    notif_count = Notification.objects.filter(
        user=request.user, is_read=False
    ).count()
    return {
        'pending_count': pending_count,
        'notif_count': notif_count,
    }


@login_required(login_url='login')
@role_required('provider')
def provider_home(request):
    station = request.user.station
    today = timezone.now().date()

    today_orders = Order.objects.filter(station=station, created_at__date=today).count()
    active_orders = Order.objects.filter(
        station=station, status__in=('assigned', 'out')
    ).count()

    today_agg = Order.objects.filter(station=station, created_at__date=today).aggregate(
        total_litres=Sum('quantity'),
        total_revenue=Sum('total_amount'),
    )
    total_litres_today = today_agg['total_litres'] or 0
    revenue_today = today_agg['total_revenue'] or 0

    pending_orders = Order.objects.filter(
        station=station, status='pending'
    ).select_related('customer')[:5]

    recent_orders = map_status_tag(Order.objects.filter(
        station=station
    ).select_related('customer').order_by('-created_at')[:10])

    stock_levels = StationStock.objects.filter(station=station).order_by('fuel_type')

    active_drivers = Driver.objects.filter(
        station=station, on_duty=True
    ).select_related('user')[:10]
    for d in active_drivers:
        d.status_css = 'busy' if d.current_order else 'available'

    context = {
        'today_orders': today_orders,
        'active_orders': active_orders,
        'total_litres_today': total_litres_today,
        'revenue_today': revenue_today,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'stock_levels': stock_levels,
        'active_drivers': active_drivers,
    }
    context.update(get_context_base(request))
    return render(request, "provider/home.html", context)


@login_required(login_url='login')
@role_required('provider')
def provider_orders(request):
    station = request.user.station
    orders = map_status_tag(Order.objects.filter(
        station=station
    ).select_related('customer').order_by('-created_at'))

    available_drivers = Driver.objects.filter(
        station=station, on_duty=True
    ).exclude(
        order__status__in=('assigned', 'out')
    )

    context = {
        'orders': orders,
        'available_drivers': available_drivers,
    }
    context.update(get_context_base(request))
    return render(request, "provider/orders.html", context)


@login_required(login_url='login')
@role_required('provider')
def provider_order_detail(request, id):
    station = request.user.station
    order = get_object_or_404(Order, id=id, station=station)
    available_drivers = Driver.objects.filter(
        station=station, on_duty=True
    ).exclude(
        order__status__in=('assigned', 'out')
    ).annotate(
        display_status=Case(
            When(on_duty=True, then=Value('available')),
            default=Value('offline'),
            output_field=CharField(),
        )
    )
    context = {
        'order': order,
        'available_drivers': available_drivers,
    }
    context.update(get_context_base(request))
    return render(request, "provider/order_detail.html", context)


@login_required(login_url='login')
@role_required('provider')
def provider_accept_order(request, id):
    station = request.user.station
    order = get_object_or_404(Order, id=id, station=station, status='pending')
    order.status = 'confirmed'
    order.confirmed_at = timezone.now()
    order.save()
    messages.success(request, f'Order #{order.id} accepted.')
    return redirect('provider_orders')


@login_required(login_url='login')
@role_required('provider')
def provider_reject_order(request, id):
    station = request.user.station
    order = get_object_or_404(Order, id=id, station=station, status='pending')
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        order.status = 'cancelled'
        order.save()
        messages.info(request, f'Order #{order.id} rejected.')
    return redirect('provider_orders')


@login_required(login_url='login')
@role_required('provider')
def provider_assign_driver(request, id):
    station = request.user.station
    if request.method == 'POST':
        order = get_object_or_404(Order, id=id, station=station, status='confirmed')
        driver_id = request.POST.get('driver_id')
        driver = get_object_or_404(Driver, id=driver_id, station=station)
        order.driver = driver
        order.status = 'assigned'
        order.driver_assigned_at = timezone.now()
        order.save()
        if messages:
            messages.success(request, f'Driver {driver.name} assigned to Order #{order.id}.')
    return redirect('provider_orders')


@login_required(login_url='login')
@role_required('provider')
def provider_stock(request):
    station = request.user.station
    stock_levels = StationStock.objects.filter(station=station).order_by('fuel_type')
    context = {'stock_levels': stock_levels}
    context.update(get_context_base(request))
    return render(request, "provider/stock.html", context)


@login_required(login_url='login')
@role_required('provider')
def provider_update_stock(request):
    station = request.user.station
    if request.method == 'POST':
        fuel_id = request.POST.get('fuel_id')
        fuel_type = request.POST.get('fuel_type')
        price = request.POST.get('price')
        litres_available = request.POST.get('litres_available')
        capacity = request.POST.get('capacity')

        if fuel_id:
            stock = get_object_or_404(StationStock, id=fuel_id, station=station)
        else:
            stock = StationStock(station=station, fuel_type=fuel_type)

        if price:
            stock.price_per_litre = price
        if litres_available:
            stock.litres_available = litres_available
        if capacity:
            stock.capacity = capacity
        stock.save()
        messages.success(request, 'Stock updated.')
    return redirect('provider_stock')


@login_required(login_url='login')
@role_required('provider')
def provider_restock(request):
    station = request.user.station
    if request.method == 'POST':
        fuel_type = request.POST.get('fuel_type')
        litres_added = request.POST.get('litres_added')
        if fuel_type and litres_added:
            stock, _ = StationStock.objects.get_or_create(
                station=station, fuel_type=fuel_type,
                defaults={'litres_available': 0, 'capacity': 5000}
            )
            stock.litres_available += int(litres_added)
            stock.save()
            messages.success(request, f'{litres_added}L added to {fuel_type}.')
    return redirect('provider_stock')


@login_required(login_url='login')
@role_required('provider')
def provider_drivers(request):
    station = request.user.station
    drivers = Driver.objects.filter(station=station).select_related('user').order_by('name')
    for d in drivers:
        d.is_active = d.status not in ('suspended', 'rejected')
        if d.status == 'approved' and d.on_duty:
            d.status_css = 'available'
        elif d.status == 'approved' and not d.on_duty:
            d.status_css = 'offline'
        elif d.status == 'pending':
            d.status_css = 'offline'
        else:
            d.status_css = 'offline'
        if d.current_order and d.on_duty:
            d.status_css = 'busy'
    context = {'drivers': drivers}
    context.update(get_context_base(request))
    return render(request, "provider/drivers.html", context)


@login_required(login_url='login')
@role_required('provider')
def provider_add_driver(request):
    station = request.user.station
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        plate = request.POST.get('plate')
        licence = request.POST.get('licence_number')
        vehicle_type = request.POST.get('vehicle_type')
        if name and phone:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            username = f"driver_{station.id}_{int(timezone.now().timestamp())}"
            user = User.objects.create_user(
                username=username,
                password='default123',
                role='driver',
                phone=phone,
            )
            Driver.objects.create(
                user=user,
                name=name,
                phone=phone,
                plate=plate or '',
                licence_number=licence or '',
                vehicle_type=vehicle_type or '',
                station=station,
                status='pending',
                is_approved=False,
            )
            messages.success(request, f'Driver {name} added.')
    return redirect('provider_drivers')


@login_required(login_url='login')
@role_required('provider')
def provider_toggle_driver(request, id):
    station = request.user.station
    if request.method == 'POST':
        driver = get_object_or_404(Driver, id=id, station=station)
        if driver.status not in ('suspended', 'rejected'):
            driver.status = 'suspended' if driver.status == 'approved' else 'approved'
            driver.is_approved = driver.status == 'approved'
            driver.save()
            return JsonResponse({'status': 'ok', 'new_status': driver.status})
    return JsonResponse({'status': 'error'}, status=400)


@login_required(login_url='login')
@role_required('provider')
def provider_reports(request):
    station = request.user.station
    period = request.GET.get('period', 7)
    try:
        period = int(period)
    except ValueError:
        period = 7

    since = timezone.now() - timedelta(days=period)
    orders_qs = Order.objects.filter(station=station, created_at__gte=since)

    total_orders = orders_qs.count()
    total_litres = orders_qs.aggregate(s=Sum('quantity'))['s'] or 0
    revenue = orders_qs.aggregate(s=Sum('total_amount'))['s'] or 0

    delivered = orders_qs.filter(status='delivered')
    total_delivered = delivered.count()
    total_delivery_seconds = 0
    count_with_times = 0
    for o in delivered:
        if o.delivered_at and o.confirmed_at:
            diff = (o.delivered_at - o.confirmed_at).total_seconds()
            total_delivery_seconds += diff
            count_with_times += 1
    avg_delivery_time = int(total_delivery_seconds / count_with_times / 60) if count_with_times else 0

    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    orders_by_day = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        count = Order.objects.filter(station=station, created_at__date=day).count()
        label = day.strftime('%a')
        orders_by_day.append({
            'count': count,
            'pct': min(count * 6, 100),
            'label': label,
        })

    if orders_by_day and max(o['count'] for o in orders_by_day) > 0:
        max_count = max(o['count'] for o in orders_by_day)
        for o in orders_by_day:
            o['pct'] = max(int((o['count'] / max_count) * 100), 5) if max_count else 0

    context = {
        'total_orders': total_orders,
        'total_litres': total_litres,
        'revenue': revenue,
        'avg_delivery_time': avg_delivery_time,
        'orders_by_day': orders_by_day,
        'period': period,
    }
    context.update(get_context_base(request))
    return render(request, "provider/reports.html", context)


@login_required(login_url='login')
@role_required('provider')
def provider_demand(request):
    context = {}
    context.update(get_context_base(request))
    return render(request, "provider/demand.html", context)


@login_required(login_url='login')
@role_required('provider')
def provider_station(request):
    context = {}
    context.update(get_context_base(request))
    return render(request, "provider/station.html", context)


@login_required(login_url='login')
@role_required('provider')
def provider_update_station(request):
    station = request.user.station
    if request.method == 'POST':
        station.name = request.POST.get('station_name', station.name)
        station.address = request.POST.get('address', station.address)
        station.phone = request.POST.get('phone', station.phone)
        station.email = request.POST.get('email', station.email)
        station.licence_no = request.POST.get('license_no', station.licence_no)
        station.delivery_radius = request.POST.get('delivery_radius', station.delivery_radius)
        station.description = request.POST.get('description', station.description)
        opening = request.POST.get('opening_time')
        closing = request.POST.get('closing_time')
        if opening:
            station.opening_time = datetime.strptime(opening, '%H:%M').time()
        if closing:
            station.closing_time = datetime.strptime(closing, '%H:%M').time()
        station.save()
        messages.success(request, 'Station settings updated.')
    return redirect('provider_station')


@login_required(login_url='login')
@role_required('provider')
def provider_toggle_open(request):
    if request.method == 'POST':
        station = request.user.station
        station.status = 'closed' if station.status == 'open' else 'open'
        station.save()
        return JsonResponse({'status': 'ok', 'is_open': station.status == 'open'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required(login_url='login')
@role_required('provider')
def provider_profile(request):
    context = {}
    context.update(get_context_base(request))
    return render(request, "provider/profile.html", context)


@login_required(login_url='login')
@role_required('provider')
def provider_update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        messages.success(request, 'Profile updated.')
    return redirect('provider_profile')


@login_required(login_url='login')
@role_required('provider')
def provider_change_password(request):
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new1 = request.POST.get('new_password1')
        new2 = request.POST.get('new_password2')
        if not request.user.check_password(old):
            messages.error(request, 'Current password is incorrect.')
        elif new1 != new2:
            messages.error(request, 'Passwords do not match.')
        elif len(new1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed.')
    return redirect('provider_profile')
