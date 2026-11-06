# Remove any navigation rows that point at Django admin (broader than 0016).

from django.db import migrations


def _is_admin_url(url: str) -> bool:
    u = (url or "").strip().lower()
    if not u:
        return False
    if "/admin" in u:
        return True
    if u.startswith("admin/") or u in ("admin", "/admin"):
        return True
    return False


def purge_admin_nav_links(apps, schema_editor):
    NavLink = apps.get_model("care", "NavLink")
    to_delete = [pk for pk, url in NavLink.objects.values_list("pk", "url") if _is_admin_url(url)]
    if to_delete:
        NavLink.objects.filter(pk__in=to_delete).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0016_remove_footer_admin_from_db"),
    ]

    operations = [
        migrations.RunPython(purge_admin_nav_links, noop),
    ]
