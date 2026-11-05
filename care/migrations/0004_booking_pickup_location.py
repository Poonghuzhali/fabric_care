from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0003_customerprofile_booking_customer"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="pickup_address",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="booking",
            name="pickup_latitude",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="pickup_longitude",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True
            ),
        ),
        migrations.AddField(
            model_name="booking",
            name="pickup_maps_url",
            field=models.URLField(blank=True, default="", max_length=500),
        ),
    ]
