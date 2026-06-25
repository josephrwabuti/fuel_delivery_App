from django.urls import path
from . import views

urlpatterns = [
    path("driver/home/", views.driver_home, name="driver_home"),
    path("driver/order/", views.driver_orders, name="driver_orders"),
    path("driver/active/", views.driver_active, name="driver_active"),
    path("driver/history/", views.driver_history, name="driver_history"),
    path("driver/earnings/", views.driver_earnings, name="driver_earnings"),
    path("driver/profile/", views.driver_profile, name="driver_profile"),
    path("driver/notifications/", views.driver_notifications, name="driver_notifications"),
    path("driver/profileupdate/", views.driver_update_profile, name="driver_update_profile"),
    path("driver/changepassword/", views.driver_change_password, name="driver_change_password"),
]