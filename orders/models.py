from django.db import models
from django.conf import settings
from accounts.models import Station, Driver


class Order(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("driver_assigned", "Driver Assigned"),
        ("en_route", "En Route"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    PAYMENT_STATUS = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    )

    FUEL_CHOICES = (
        ("Petrol", "Petrol"),
        ("Diesel", "Diesel"),
        ("Kerosene", "Kerosene"),
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )

    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)

    delivery_address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)

    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="pending"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)