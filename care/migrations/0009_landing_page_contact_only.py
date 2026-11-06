from django.db import migrations, models


def book_urls_to_contact(apps, schema_editor):
    HeroSlide = apps.get_model("care", "HeroSlide")
    CallToAction = apps.get_model("care", "CallToAction")
    NavLink = apps.get_model("care", "NavLink")
    HeroSlide.objects.filter(primary_url="#book").update(primary_url="#contact")
    CallToAction.objects.filter(button_url="#book").update(button_url="#contact")
    NavLink.objects.filter(url="#book").update(url="#contact")


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0008_backfill_customer_addresses"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesetting",
            name="enquiry_inbox_email",
            field=models.EmailField(
                blank=True,
                help_text="Optional. If set, contact form submissions are emailed here instead of the main Email field.",
                max_length=254,
            ),
        ),
        migrations.AlterField(
            model_name="calltoaction",
            name="button_url",
            field=models.CharField(default="#contact", max_length=200),
        ),
        migrations.AlterField(
            model_name="heroslide",
            name="primary_url",
            field=models.CharField(
                default="#contact",
                help_text="Use #contact to scroll to the contact section, or a full URL.",
                max_length=200,
            ),
        ),
        migrations.RunPython(book_urls_to_contact, migrations.RunPython.noop),
    ]
