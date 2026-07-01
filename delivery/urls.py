from django.urls import path
from . import views

urlpatterns = [
    path("", views.driver_home, name="driver_home"),
    path("orders/", views.driver_orders, name="driver_orders"),
    path("active/", views.driver_active, name="driver_active"),
    path("earnings/", views.driver_earnings, name="driver_earnings"),
    path("history/", views.driver_history, name="driver_history"),
    path("profile/", views.driver_profile, name="driver_profile"),
    path("notifications/", views.driver_notifications, name="driver_notifications"),
    path("update-profile/", views.driver_update_profile, name="driver_update_profile"),
    path("change-password/", views.driver_change_password, name="driver_change_password"),
    path("update-status/<int:order_id>/", views.driver_update_status, name="driver_update_status"),
    path("report-issue/<int:order_id>/", views.driver_report_issue, name="driver_report_issue"),
    path("update-location/", views.driver_update_location, name="driver_update_location"),
    path("toggle-duty/", views.driver_toggle_duty, name="driver_toggle_duty"),
]