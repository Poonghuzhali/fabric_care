# Remove navigation rows that still point at Django admin (including full URLs).

from django.db import migrations


def _blocked(u: str) -> bool:
    from care.public_site import is_public_nav_url

    return not is_public_nav_url(u or "")


def purge_admin_nav_entries(apps, schema_editor):
    NavLink = apps.get_model("care", "NavLink")
    to_delete = [pk for pk, url in NavLink.objects.values_list("pk", "url") if _blocked(url)]
    if to_delete:
        NavLink.objects.filter(pk__in=to_delete).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("care", "0021_nav_links_brochure"),
    ]

    operations = [
        migrations.RunPython(purge_admin_nav_entries, noop),
    ]
