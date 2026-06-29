from django.urls import path
from . import views

urlpatterns = [
    path('customer/register/', views.register_dispatch, name='customer_register'),
    path('customer/login/', views.login_dispatch, name='customer_login'),

    path('driver/register/', views.register_dispatch, name='driver_register'),
    path('driver/login/', views.login_dispatch, name='driver_login'),

    path('provider/register/', views.register_dispatch, name='provider_register'),
    path('provider/login/', views.login_dispatch, name='provider_login'),
]