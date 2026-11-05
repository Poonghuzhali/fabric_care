from django.db import migrations


def backfill_from_bookings(apps, schema_editor):
    Booking = apps.get_model("care", "Booking")
    CustomerAddress = apps.get_model("care", "CustomerAddress")
    seen = set()
    for booking in Booking.objects.filter(customer_id__isnull=False).order_by("created_at"):
        if booking.pickup_latitude is None or booking.pickup_longitude is None:
            continue
        normalized = " ".join((booking.pickup_address or "").split()).lower()
        if len(normalized) < 10:
            continue
        key = (booking.customer_id, normalized)
        if key in seen:
            continue
        seen.add(key)
        is_first = not CustomerAddress.objects.filter(customer_id=booking.customer_id).exists()
        CustomerAddress.objects.create(
            customer_id=booking.customer_id,
            label="Home" if is_first else f"Address {CustomerAddress.objects.filter(customer_id=booking.customer_id).count() + 1}",
            address=" ".join(booking.pickup_address.split()),
            latitude=booking.pickup_latitude,
            longitude=booking.pickup_longitude,
            maps_url=booking.pickup_maps_url or "",
            is_default=is_first,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0007_customeraddress"),
    ]

    operations = [
        migrations.RunPython(backfill_from_bookings, migrations.RunPython.noop),
    ]
