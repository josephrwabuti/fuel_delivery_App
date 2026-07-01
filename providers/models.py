from django.db import models
from django.conf import settings


class StationStock(models.Model):
    FUEL_TYPES = [
        ("Petrol", "Petrol"),
        ("Diesel", "Diesel"),
        ("Kerosene", "Kerosene"),
    ]

    station = models.ForeignKey(
        'accounts.Station', on_delete=models.CASCADE,
        related_name='stock_levels'
    )
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES)
    litres_available = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    capacity = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    price_per_litre = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.station.name} - {self.fuel_type}"

    @property
    def type(self):
        return self.fuel_type

    @property
    def pct(self):
        if self.capacity == 0:
            return 0
        return int((self.litres_available / self.capacity) * 100)

    @property
    def updated_at(self):
        return self.last_updated

    @property
    def price(self):
        return self.price_per_litre