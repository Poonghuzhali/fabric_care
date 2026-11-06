from django.db import migrations, models


def set_order_now_labels(apps, schema_editor):
    Service = apps.get_model("care", "Service")
    for s in Service.objects.all():
        label = (getattr(s, "book_button_label", None) or "").strip()
        if label in ("", "Book"):
            s.book_button_label = "Order Now"
        url = (getattr(s, "book_button_url", None) or "").strip()
        if not url:
            s.book_button_url = "#contact"
        s.save(update_fields=["book_button_label", "book_button_url"])


class Migration(migrations.Migration):
    dependencies = [
        ("care", "0023_landing_cms_and_sections"),
    ]

    operations = [
        migrations.AlterField(
            model_name="service",
            name="book_button_label",
            field=models.CharField(blank=True, default="Order Now", max_length=60),
        ),
        migrations.RunPython(set_order_now_labels, migrations.RunPython.noop),
    ]
