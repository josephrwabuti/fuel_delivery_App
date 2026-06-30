from django.contrib import admin
from .models import User, CustomerProfile, Driver, Station


admin.site.register(User)
admin.site.register(CustomerProfile)
admin.site.register(Driver)


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'status')   
    list_filter = ('status',)                      
    actions = ['approve_stations', 'reject_stations']

    def approve_stations(self, request, queryset):
        queryset.update(status='approved')

    def reject_stations(self, request, queryset):
        queryset.update(status='rejected')

    approve_stations.short_description = "Approve selected stations"
    reject_stations.short_description = "Reject selected stations"