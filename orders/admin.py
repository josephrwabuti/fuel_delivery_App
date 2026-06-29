from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "station",
        "fuel_type",
        "quantity",
        "status",
        "payment_status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
        "fuel_type",
        "created_at",
    )

    search_fields = (
        "customer__username",
        "customer__first_name",
        "customer__last_name",
        "station__name",
    )

    ordering = ("-created_at",)