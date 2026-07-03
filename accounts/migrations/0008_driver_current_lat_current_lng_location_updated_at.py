# Generated manually — adds live location tracking fields to Driver

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_driver_alter_station_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="driver",
            name="current_lat",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="driver",
            name="current_lng",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="driver",
            name="location_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
