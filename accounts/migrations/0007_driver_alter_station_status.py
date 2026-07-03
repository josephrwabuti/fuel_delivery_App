# Generated manually — adds "assigned" to Driver status choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_station_is_open_alter_station_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="driver",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("assigned", "Assigned"),
                    ("rejected", "Rejected"),
                    ("suspended", "Suspended"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
