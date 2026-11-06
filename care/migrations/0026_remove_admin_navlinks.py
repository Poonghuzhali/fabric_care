from django.db import migrations


def purge_non_public_nav(apps, schema_editor):
    from care.public_site import is_public_nav_item

    NavLink = apps.get_model("care", "NavLink")
    to_delete = []
    for pk, label, url in NavLink.objects.values_list("pk", "label", "url"):
        if not is_public_nav_item((label or "").strip(), (url or "").strip()):
            to_delete.append(pk)
    if to_delete:
        NavLink.objects.filter(pk__in=to_delete).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("care", "0025_backfill_service_prices"),
    ]

    operations = [
        migrations.RunPython(purge_non_public_nav, migrations.RunPython.noop),
    ]
