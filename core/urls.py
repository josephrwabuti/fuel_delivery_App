from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("customer/home/", views.customer_home, name="customer_home"),
    path("customer/stations/", views.customer_stations, name="customer_stations"),
    path("customer/order/", views.customer_order, name="customer_order"),
    path("customer/tracking/", views.customer_tracking, name="customer_tracking"),
    path("customer/history/", views.customer_history, name="customer_history"),
    path("customer/profile/", views.customer_profile, name="customer_profile"),
    path("customer/notifications/", views.customer_notifications, name="customer_notifications"),
    path("customer/profileupdate/", views.customer_update_profile, name="customer_update_profile"),
    path("customer/changepassword/", views.customer_change_password, name="customer_change_password"),
    path("customer/deleteaccount/", views.customer_delete_account, name="customer_delete_account"),
    path("customer/placeorder/", views.customer_place_order, name="customer_place_order"),
]