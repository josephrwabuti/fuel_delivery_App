from django.contrib import admin
from .models import User, CustomerProfile, Driver, Station

admin.site.register(User)
admin.site.register(CustomerProfile)
admin.site.register(Driver)
admin.site.register(Station)