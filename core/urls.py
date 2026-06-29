from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('customer/dashboard/', views.customer_home, name='customer_home'),
    path('provider/dashboard/', views.provider_home, name='provider_home'),
    path('driver/dashboard/', views.driver_home, name='driver_home'),
    path('admin/dashboard/', views.admin_home, name='admin_home'),

    path(
        "customer/stations/",
        views.customer_stations,
        name="customer_stations",
    ),

    path(
        "customer/order/",
        views.customer_order,
        name="customer_order",
    ),

    path(
        "customer/tracking/",
        views.customer_tracking,
        name="customer_tracking",
    ),

    path(
        "customer/history/",
        views.customer_history,
        name="customer_history",
    ),
    path(
        "customer/profile/",
        views.customer_profile,
        name="customer_profile",
    ),
    path(
        "customer/notifications/",
        views.customer_notifications,
        name="customer_notifications",
    ),
    path(
        'customer/update-profile/', views.customer_update_profile, name='customer_update_profile'
    ),
    path(
        'customer/change-password/', views.customer_change_password, name='customer_change_password'
    ),
    path(
        'customer/delete-account/', views.customer_delete_account, name='customer_delete_account'
    ),
    path(
        'customer/place-order/', views.customer_place_order, name='customer_place_order'
    ),
]
