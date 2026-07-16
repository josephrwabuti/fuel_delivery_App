from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomerProfile, Driver, Station, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Extra', {'fields': ('role', 'phone')}),
    )

# Customer Profile
admin.site.register(CustomerProfile)

# Driver
admin.site.register(Driver)


# Station Admin
@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'status', 'is_open')
    list_filter = ('status', 'is_open')
    actions = ['approve_stations', 'reject_stations']

    def approve_stations(self, request, queryset):
        queryset.update(status='approved')

    def reject_stations(self, request, queryset):
        queryset.update(status='rejected')

    approve_stations.short_description = "Approve selected stations"
    reject_stations.short_description = "Reject selected stations"