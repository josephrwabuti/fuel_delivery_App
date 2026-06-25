from django.db import models
from django.contrib.auth.models import User


class Station(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    is_open = models.BooleanField(default=True)
    rating = models.FloatField(default=4.5)

    def __str__(self):
        return self.name
    
    
class FuelStock(models.Model):
    FUEL_TYPES = [
        ("Petrol", "Petrol"),
        ("Diesel", "Diesel"),
        ("Kerosene", "Kerosene"),
    ]

    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="fuels")
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.IntegerField()
    litres_available = models.IntegerField()

    def __str__(self):
        return f"{self.station.name} - {self.fuel_type}"
    
    
class Order(models.Model):

    STATUS = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("delivering", "Delivering"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    station = models.ForeignKey(Station, on_delete=models.CASCADE)

    fuel_type = models.CharField(max_length=20)
    quantity = models.IntegerField()

    driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries"
    )

    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}"