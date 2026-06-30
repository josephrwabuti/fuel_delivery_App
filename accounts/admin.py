from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import CustomerProfile, Driver, Station

User = get_user_model()

# User admin
admin.site.register(User)

# Customer Profile
admin.site.register(CustomerProfile)

# Driver
admin.site.register(Driver)


# Station Admin
@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'status')
    list_filter = ('status',)
    actions = ['approve_stations', 'reject_stations']

    def approve_stations(self, request, queryset):
        queryset.update(status='open')

    def reject_stations(self, request, queryset):
        queryset.update(status='closed')

    approve_stations.short_description = "Approve selected stations"
    reject_stations.short_description = "Reject selected stations"