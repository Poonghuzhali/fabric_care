from decimal import Decimal

from django.db import migrations

# Placeholder prices aligned with seed data (brochure-style grid)
SERVICE_PRICES_BY_NAME = {
    "Saree Rolling": Decimal("150.00"),
    "Towel Ironing & Refreshing": Decimal("80.00"),
    "Coat & Delicate Fabric Steam Refresh": Decimal("350.00"),
    "Cotton Veshti Starching & Polishing": Decimal("120.00"),
    "Silk Veshti Polishing": Decimal("200.00"),
    "Bed Sheet & Cover Ironing": Decimal("180.00"),
    "Saree Pre-Pleating": Decimal("450.00"),
    "Saree Polishing": Decimal("280.00"),
    "Cotton Saree Starching & Polishing": Decimal("220.00"),
    "Saree Folding": Decimal("100.00"),
}


def backfill_prices(apps, schema_editor):
    Service = apps.get_model("care", "Service")
    for s in Service.objects.filter(price_amount__isnull=True):
        name = (getattr(s, "name", None) or "").strip()
        if name not in SERVICE_PRICES_BY_NAME:
            continue
        s.price_amount = SERVICE_PRICES_BY_NAME[name]
        s.save(update_fields=["price_amount"])


class Migration(migrations.Migration):
    dependencies = [
        ("care", "0024_service_book_button_order_now_default"),
    ]

    operations = [
        migrations.RunPython(backfill_prices, migrations.RunPython.noop),
    ]
