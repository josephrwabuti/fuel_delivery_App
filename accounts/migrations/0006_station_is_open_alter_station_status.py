# Generated manually — adds is_open field, updates status choices, migrates existing data

from django.db import migrations, models


def migrate_existing_status(apps, schema_editor):
    Station = apps.get_model("accounts", "Station")
    # "open" → approved & is_open=True (default)
    Station.objects.filter(status="open").update(status="approved")
    # "closed" → approved & is_open=False
    Station.objects.filter(status="closed").update(status="approved", is_open=False)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_station_closing_time_station_delivery_radius_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="station",
            name="is_open",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="station",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                default="pending",
                max_length=10,
            ),
        ),
        migrations.RunPython(migrate_existing_status, reverse_code=migrations.RunPython.noop),
    ]
