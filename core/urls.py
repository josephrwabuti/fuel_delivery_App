from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('provider/dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
]
