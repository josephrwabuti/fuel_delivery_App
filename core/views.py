from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import role_required
from orders.forms import OrderForm
from accounts.models import Station
from orders.models import Order
from django.contrib.auth.models import User



def home(request):
    return render(request, 'core/index.html')


@login_required(login_url='login')
@role_required('customer')
def customer_home(request):
    return render(request, 'customer/home.html')


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

def customer_stations(request):
    stations = Station.objects.filter(is_approved=True)

    context = {
        "stations": stations
    }
    return render(request, "customer/stations.html", context)


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
    stations = Station.objects.all()
    return render(request, 'admin_panel/stations.html', {"stations": stations})

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