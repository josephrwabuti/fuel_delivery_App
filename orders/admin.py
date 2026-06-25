from django.contrib import admin
from .models import Station, FuelStock, Order

admin.site.register(Station)
admin.site.register(FuelStock)
admin.site.register(Order)