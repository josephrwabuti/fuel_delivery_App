from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    
]
