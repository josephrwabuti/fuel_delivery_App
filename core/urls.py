from django.urls import path
from . import views
from delivery import views as delivery_views

urlpatterns = [
    path("", views.home, name="home"),
    path('customer/dashboard/', views.customer_home, name='customer_home'),
    path('provider/dashboard/', views.provider_home, name='provider_home'),
    path('driver/dashboard/', delivery_views.driver_home, name='driver_home'),
    path('dashboard/admin/', views.admin_home, name='admin_home'),

    path("customer/stations/", views.stations_view, name="customer_stations"),

    path( "customer/order/", views.create_order, name="customer_order"),

    path( "customer/tracking/", views.tracking_view, name="customer_tracking" ),

    path("customer/history/", views.history_view, name="customer_history"),
    
    path("order/confirm/<int:order_id>/", views.confirm_delivery, name="customer_confirm_delivery"),
    
    path("order/cancel/<int:order_id>/", views.cancel_order, name="customer_cancel_order"),
    
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
    path(
        'customer/notifications/<int:notif_id>/dismiss/', views.dismiss_notification, name='dismiss_notification'
    ),
    path(
        'customer/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'
    ),
    path(
        'notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read_any'
    ),
    
    path('dashboard/admin/stations/', views.admin_stations, name='admin_stations'),
    path('dashboard/admin/station/approve/<int:station_id>/', views.approve_station, name='approve_station'),
    path('dashboard/admin/station/reject/<int:station_id>/', views.reject_station, name='reject_station'),
    path('dashboard/admin/driver/approve/<int:driver_id>/', views.approve_driver, name='approve_driver'),
    path('dashboard/admin/driver/assign/<int:driver_id>/', views.assign_driver_station, name='assign_driver_station'),
    path('dashboard/admin/driver/reject/<int:driver_id>/', views.reject_driver, name='reject_driver'),
    path('dashboard/admin/driver/suspend/<int:driver_id>/', views.suspend_driver, name='suspend_driver'),
    path('drivers/', views.admin_drivers, name='admin_drivers'),
    path('orders/', views.admin_orders, name='admin_orders'),
    path('customers/', views.admin_customers, name='admin_customers'),
    path('reports/', views.admin_reports, name='admin_reports'),
    path('demand/', views.admin_demand, name='admin_demand'),
    path('activity/', views.admin_activity, name='admin_activity'),
    path('settings/', views.admin_settings, name='admin_settings'),
    path('profile/', views.admin_profile, name='admin_profile'),
    path('save-settings/', views.admin_save_settings, name='admin_save_settings'),
    path('update-profile/', views.admin_update_profile, name='admin_update_profile'),
    path('change-password/', views.admin_change_password, name='admin_change_password'),
    
]
