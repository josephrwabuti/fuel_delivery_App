from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomerProfile, Customer, Driver, Station, User


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


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'get_phone', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    list_filter = ('is_active', 'date_joined')
    ordering = ('-date_joined',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='customer')

    def get_phone(self, obj):
        return obj.phone or ''
    get_phone.short_description = 'Phone'


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)


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