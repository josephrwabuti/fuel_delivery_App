from django.contrib import admin
from .models import User, CustomerProfile, Driver, Station
from .models import Station

admin.site.register(User)
admin.site.register(CustomerProfile)
admin.site.register(Driver)

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'is_approved')
    list_filter = ('is_approved',)
    actions = ['approve_stations']

    def approve_stations(self, request, queryset):
        queryset.update(is_approved=True)
    approve_stations.short_description = "Approve selected stations"