from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    vehicle_number = models.CharField(max_length=30)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.user.get_full_name()
    
class DeliveryTracking(models.Model):
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)