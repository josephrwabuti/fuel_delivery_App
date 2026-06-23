from django.urls import path
from . import views

urlpatterns = [
    path('customer/login/', views.customer_login, name='customer_login'),
    path('customer/register/', views.customer_register, name='customer_register'),

    path('provider/login/', views.provider_login, name='provider_login'),

    path('driver/login/', views.driver_login, name='driver_login'),

    path('admin/login/', views.admin_login, name='admin_login'),
]