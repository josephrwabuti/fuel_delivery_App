from django.urls import path
from . import views

urlpatterns = [

    path("dashboard/", views.provider_home, name="provider_home"),

    path("orders/", views.provider_orders, name="provider_orders"),

    path("orders/<int:id>/", views.provider_order_detail,
         name="provider_order_detail"),

    path("orders/<int:id>/accept/",
         views.provider_accept_order,
         name="provider_accept_order"),

    path("orders/<int:id>/reject/",
         views.provider_reject_order,
         name="provider_reject_order"),

    path("stock/", views.provider_stock,
         name="provider_stock"),

    path("drivers/", views.provider_drivers,
         name="provider_drivers"),

    path("reports/", views.provider_reports,
         name="provider_reports"),
    
     path("demand/", views.provider_demand,
         name="provider_demand"),
     
     path("station/", views.provider_station,
         name="provider_station"),
     
     path("profile/", views.provider_profile, name="provider_profile"),
     
     path("profile/change-password", views.provider_change_password, name="provider_change_password"),
     
     path("profile/update", views.provider_update_profile, name="provider_update_profile"),
     
     path("stock/update/", views.provider_update_stock, name="provider_update_stock"),
     
     path("stock/restock/", views.provider_restock, name="provider_restock"),
     
     path("provider/driver/", views.provider_add_driver, name="provider_add_driver"),
     
     path("station/update", views.provider_update_station,
         name="provider_update_station"),
]