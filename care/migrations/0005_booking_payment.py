from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0004_booking_pickup_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="amount_paid",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0"),
                max_digits=10,
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="payment_order_id",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="booking",
            name="payment_id",
            field=models.CharField(blank=True, max_length=80, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="payment_status",
            field=models.CharField(
                choices=[
                    ("unpaid", "Unpaid"),
                    ("paid", "Paid"),
                    ("failed", "Failed"),
                ],
                default="unpaid",
                max_length=20,
            ),
        ),
    ]
