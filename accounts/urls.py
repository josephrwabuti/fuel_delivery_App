from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("admin/home/", views.admin_home, name="admin_home"),
    path("admin/stations/", views.admin_stations, name="admin_stations"),
    path("admin/drivers/", views.admin_drivers, name="admin_drivers"),
    path("admin/orders/", views.admin_orders, name="admin_orders"),
    path("admin/reports/", views.admin_reports, name="admin_reports"),
    path("admin/activity/", views.admin_activity, name="admin_activity"),
]