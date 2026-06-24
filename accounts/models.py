from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

# ================= VALIDATORS FIRST =================
phone_validator = RegexValidator(
    regex=r'^\d{9}$',
    message="Phone number must be 9 digits"
)

driver_license_validator = RegexValidator(
    regex=r'^\d{11}$',
    message="Driver license must be 11 digits"
)

business_license_validator = RegexValidator(
    regex=r'^\d{12}$',
    message="Business license must be 12 digits"
)

# ================= MODEL =================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone = models.CharField(
        max_length=9,
        validators=[phone_validator]
    )

    license_number = models.CharField(
        max_length=11,
        validators=[driver_license_validator],
        null=True,
        blank=True
    )

    license_no = models.CharField(
        max_length=12,
        validators=[business_license_validator],
        null=True,
        blank=True
    )