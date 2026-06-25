from django.db import models

# Create your models here.
class DailyReport(models.Model):
    station = models.ForeignKey("orders.Station", on_delete=models.CASCADE)
    date = models.DateField()

    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)