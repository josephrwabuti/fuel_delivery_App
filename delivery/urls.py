from django.urls import path
from . import views

urlpatterns = [
    path("orders/", views.driver_orders, name="driver_orders"),
    path("active/", views.driver_active, name="driver_active"),
    path("earnings/", views.driver_earnings, name="driver_earnings"),
    path("history/", views.driver_history, name="driver_history"),
    path("driver/profile/", views.driver_profile, name="driver_profile"),
    path("driver/notifications/", views.driver_notifications, name="driver_notifications"),
    path("driver/update-profile/", views.driver_update_profile, name="driver_update_profile"),
    path("driver/change-password/", views.driver_change_password, name="driver_change_password"),
]