from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

# ================= VALIDATORS =================

phone_validator = RegexValidator(
    regex=r'^\d{9}$',
    message="Phone number must be exactly 9 digits."
)

driver_license_validator = RegexValidator(
    regex=r'^\d{11}$',
    message="Driver license number must be exactly 11 digits."
)

business_license_validator = RegexValidator(
    regex=r'^\d{12}$',
    message="Business license number must be exactly 12 digits."
)

# ================= PROFILE MODEL =================

class Profile(models.Model):

    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("provider", "Provider"),
        ("driver", "Driver"),
        ("admin", "Admin"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="customer"
    )

    phone = models.CharField(
        max_length=9,
        validators=[phone_validator],
        blank=True,
        null=True
    )

    # Driver License (only for driver)
    license_number = models.CharField(
        max_length=11,
        validators=[driver_license_validator],
        blank=True,
        null=True
    )

    # Business License (only for provider)
    license_no = models.CharField(
        max_length=12,
        validators=[business_license_validator],
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"