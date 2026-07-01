from django.db import models
from django.conf import settings


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class PlatformSettings(models.Model):
    platform_name = models.CharField(max_length=255, default="FuelGo")
    support_email = models.EmailField(default="support@fuelgo.co.tz")
    support_phone = models.CharField(max_length=50, default="+255 700 000 000")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    max_radius = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    order_timeout = models.IntegerField(default=15)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Platform settings"

    def __str__(self):
        return self.platform_name
