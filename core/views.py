from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import role_required
from orders.forms import OrderForm
from accounts.models import Station
from orders.models import Order



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