from django.urls import path
from . import views

urlpatterns = [
    path("", views.pwa_index, name="pwa_index"),
    path("csrf/", views.csrf_token, name="pwa_csrf"),

    # Auth
    path("api/login/", views.api_login, name="api_login"),
    path("api/register/", views.api_register, name="api_register"),
    path("api/logout/", views.api_logout, name="api_logout"),
    path("api/user/", views.api_user, name="api_user"),

    # Customer
    path("api/customer/dashboard/", views.api_customer_dashboard, name="api_customer_dashboard"),
    path("api/customer/stations/", views.api_stations, name="api_stations"),
    path("api/customer/order/", views.api_create_order, name="api_create_order"),
    path("api/customer/tracking/", views.api_tracking, name="api_tracking"),
    path("api/customer/history/", views.api_history, name="api_history"),
    path("api/customer/order/<int:order_id>/cancel/", views.api_cancel_order, name="api_cancel_order"),
    path("api/customer/order/<int:order_id>/confirm/", views.api_confirm_delivery, name="api_confirm_delivery"),
    path("api/customer/profile/", views.api_customer_profile, name="api_customer_profile"),
    path("api/customer/profile/update/", views.api_customer_update_profile, name="api_customer_update_profile"),
    path("api/customer/profile/change-password/", views.api_customer_change_password, name="api_customer_change_password"),
    path("api/customer/notifications/", views.api_customer_notifications, name="api_customer_notifications"),

    # Driver
    path("api/driver/dashboard/", views.api_driver_dashboard, name="api_driver_dashboard"),
    path("api/driver/orders/", views.api_driver_orders, name="api_driver_orders"),
    path("api/driver/active/", views.api_driver_active, name="api_driver_active"),
    path("api/driver/order/<int:order_id>/update-status/", views.api_driver_update_status, name="api_driver_update_status"),
    path("api/driver/update-location/", views.api_driver_update_location, name="api_driver_update_location"),
    path("api/driver/toggle-duty/", views.api_driver_toggle_duty, name="api_driver_toggle_duty"),
    path("api/driver/earnings/", views.api_driver_earnings, name="api_driver_earnings"),
    path("api/driver/history/", views.api_driver_history, name="api_driver_history"),
    path("api/driver/profile/", views.api_driver_profile, name="api_driver_profile"),
    path("api/driver/profile/update/", views.api_driver_update_profile, name="api_driver_update_profile"),
    path("api/driver/notifications/", views.api_driver_notifications, name="api_driver_notifications"),

    # Notifications (shared)
    path("api/notifications/<int:notif_id>/dismiss/", views.api_dismiss_notification, name="api_dismiss_notification"),
    path("api/notifications/mark-all-read/", views.api_mark_notifications_read, name="api_mark_notifications_read"),
]
