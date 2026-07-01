from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('provider', 'Station Owner'),
        ('driver', 'Driver'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True)


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)


class Station(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="station"
    )

    name = models.CharField(max_length=255)
    address = models.TextField()
    lat = models.FloatField()
    lng = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    rating = models.FloatField(default=0)
    review_count = models.IntegerField(default=0)
    hours = models.CharField(max_length=100, default="24/7")
    phone = models.CharField(max_length=20, blank=True)
    licence_no = models.CharField(max_length=100, blank=True)
    fuel_types = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_approved(self):
        return self.status == "approved"

    def __str__(self):
        return self.name

    
    
class FuelPrice(models.Model):
    station = models.ForeignKey(Station, related_name="fuels", on_delete=models.CASCADE)
    FUEL_TYPES = [
        ("Petrol", "Petrol"),
        ("Diesel", "Diesel"),
        ("Kerosene", "Kerosene"),
    ]

    type = models.CharField(max_length=20, choices=FUEL_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.station.name} - {self.type}"
    

class Driver(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("suspended", "Suspended"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default="Unknown")
    phone = models.CharField(max_length=20)
    plate = models.CharField(max_length=20, blank=True)
    rating = models.FloatField(default=5)

    licence_number = models.CharField(max_length=50, blank=True)
    plate_number = models.CharField(max_length=20, blank=True)
    vehicle_type = models.CharField(max_length=50, blank=True)
    is_approved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    on_duty = models.BooleanField(default=False)
    station = models.ForeignKey(
        'accounts.Station', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='drivers'
    )

    def __str__(self):
        return self.name

class StationReview(models.Model):
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name="review")
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)