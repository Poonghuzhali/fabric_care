# Remove navigation rows whose label advertises admin (any word "admin").

import re

from django.db import migrations

_ADMIN_IN_LABEL = re.compile(r"(?<![a-z])admin(?![a-z])", re.IGNORECASE)


def purge_admin_labeled_links(apps, schema_editor):
    NavLink = apps.get_model("care", "NavLink")
    for pk, label in NavLink.objects.values_list("pk", "label"):
        if label and _ADMIN_IN_LABEL.search(label):
            NavLink.objects.filter(pk=pk).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0018_scrub_legacy_admin_booking_copy"),
    ]

    operations = [
        migrations.RunPython(purge_admin_labeled_links, noop),
    ]
