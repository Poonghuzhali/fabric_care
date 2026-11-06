# Ensure public navigation matches the brochure layout (Pricing, How it Works, etc.).

from django.db import migrations


def sync_brochure_nav(apps, schema_editor):
    NavLink = apps.get_model("care", "NavLink")

    labels_lower = {str(x or "").strip().lower() for x in NavLink.objects.values_list("label", flat=True)}
    expected = {
        "home",
        "about us",
        "services",
        "pricing",
        "how it works",
        "reviews",
        "contact",
    }

    if labels_lower != expected:
        NavLink.objects.all().delete()
        seed_links = [
            ("Home", "#home", 1),
            ("About Us", "#about", 2),
            ("Services", "#services", 3),
            ("Pricing", "#pricing", 4),
            ("How it Works", "#how-it-works", 5),
            ("Reviews", "#testimonials", 6),
            ("Contact", "#contact", 7),
        ]
        for label, url, order in seed_links:
            NavLink.objects.create(label=label, url=url, order=order)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0020_sitesetting_service_read_more_and_design_defaults"),
    ]

    operations = [
        migrations.RunPython(sync_brochure_nav, noop),
    ]
