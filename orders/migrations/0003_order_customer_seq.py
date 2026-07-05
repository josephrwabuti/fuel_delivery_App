# Generated manually

from django.db import migrations, models


def backfill_customer_seq(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    from django.db.models import Count, Min

    customer_ids = Order.objects.values_list("customer_id", flat=True).distinct()
    for cid in customer_ids:
        orders = Order.objects.filter(customer_id=cid).order_by("created_at", "id")
        for i, order in enumerate(orders, start=1):
            Order.objects.filter(id=order.id).update(customer_seq=i)


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_order_customer_lat_order_customer_lng_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="customer_seq",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(backfill_customer_seq, reverse_code=migrations.RunPython.noop),
    ]
