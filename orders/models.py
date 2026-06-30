from django.db import models
from django.conf import settings



class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("assigned", "Driver Assigned"),
        ("out", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    station = models.ForeignKey('accounts.Station', on_delete=models.CASCADE)
    driver = models.ForeignKey('accounts.Driver', null=True, blank=True, on_delete=models.SET_NULL)

    fuel_type = models.CharField(max_length=20)
    quantity = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # 🔥 ADD THESE NEW FIELDS
    delivery_address = models.TextField()
    phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    driver_assigned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id}"
    
    
