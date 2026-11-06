# Add service_read_more_label; align defaults with brochure-style landing page.

from django.db import migrations, models


def set_design_defaults(apps, schema_editor):
    SiteSetting = apps.get_model("care", "SiteSetting")
    HeroSlide = apps.get_model("care", "HeroSlide")

    for row in SiteSetting.objects.all():
        if not (getattr(row, "service_read_more_label", "") or "").strip():
            row.service_read_more_label = "Read more"
        nc = (getattr(row, "nav_contact_label", "") or "").strip()
        if nc.lower() in ("", "contact us"):
            row.nav_contact_label = "Book a Service"
        row.save(update_fields=["service_read_more_label", "nav_contact_label"])

    for slide in HeroSlide.objects.all():
        pl = (slide.primary_label or "").strip()
        pu = (slide.primary_url or "").strip()
        pl_l = pl.lower()
        pu_l = pu.lower()
        if pl_l == "contact us" or (pu_l in ("#contact", "") and "book" not in pl_l):
            slide.primary_label = "Book Now"
            slide.primary_url = "#contact"
        sl = (slide.secondary_label or "").strip()
        if sl.lower() == "our services":
            slide.secondary_label = "Our Services"
            slide.secondary_url = slide.secondary_url or "#services"
        slide.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0019_remove_nav_links_with_admin_in_label"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesetting",
            name="service_read_more_label",
            field=models.CharField(
                blank=True,
                default="Read more",
                help_text="Shown on each service card (opens detail).",
                max_length=40,
            ),
        ),
        migrations.AlterField(
            model_name="sitesetting",
            name="nav_contact_label",
            field=models.CharField(
                blank=True,
                default="Book a Service",
                help_text="Primary button in the header (usually scrolls to contact).",
                max_length=60,
            ),
        ),
        migrations.RunPython(set_design_defaults, noop),
    ]
