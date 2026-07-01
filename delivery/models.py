from django.db import models
from django.conf import settings


class DeliveryLog(models.Model):
    STATUS_CHOICES = [
        ("assigned", "Assigned"),
        ("picked_up", "Picked Up"),
        ("delivering", "Delivering"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
    ]

    order = models.OneToOneField(
        'orders.Order', on_delete=models.CASCADE,
        related_name='delivery_log'
    )
    driver = models.ForeignKey(
        'accounts.Driver', on_delete=models.CASCADE,
        related_name='delivery_logs'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="assigned")
    driver_earning = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delivery #{self.order_id} - {self.driver.name}"