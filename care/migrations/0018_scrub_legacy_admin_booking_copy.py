# Clean legacy admin/booking strings still stored on older databases.

import re

from django.db import migrations

DEFAULT_COPYRIGHT = "© 2026 Vastra Care. All rights reserved."
DEFAULT_CONTACT = "Contact us"
_ADMIN_LABELS = {"admin", "django admin", "site admin"}
_ADMIN_FOOTER = re.compile(
    r"django\s*admin|edit\s*site\s*content|/\s*admin\b",
    re.IGNORECASE,
)


def _bad_nav_url(url: str) -> bool:
    u = (url or "").strip().lower()
    if not u:
        return False
    if u in {"admin", "/admin", "#admin", "/admin/"}:
        return True
    if "/admin" in u or u.startswith("admin/"):
        return True
    if u.startswith("#") and "admin" in u:
        return True
    return False


def _bad_nav_label(label: str) -> bool:
    return (label or "").strip().lower() in _ADMIN_LABELS


def _copyright_ok(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return DEFAULT_COPYRIGHT
    lower = raw.lower()
    if "django admin" in lower or "edit site content" in lower or "/admin" in lower:
        cleaned = re.split(r"\s*[—\-–]\s*", raw, maxsplit=1)[0].strip()
        if _ADMIN_FOOTER.search(cleaned):
            cleaned = _ADMIN_FOOTER.sub("", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" —-–")
        if not cleaned or len(cleaned) < 6:
            return DEFAULT_COPYRIGHT
        return cleaned[:180]
    return raw[:180]


def scrub(apps, schema_editor):
    NavLink = apps.get_model("care", "NavLink")
    SiteSetting = apps.get_model("care", "SiteSetting")
    HeroSlide = apps.get_model("care", "HeroSlide")

    for link in NavLink.objects.all():
        if _bad_nav_url(link.url) or _bad_nav_label(link.label):
            link.delete()

    for row in SiteSetting.objects.all():
        row.copyright_text = _copyright_ok(getattr(row, "copyright_text", "") or "")
        nc = (getattr(row, "nav_contact_label", "") or "").strip()
        if not nc or re.search(r"\bbook\b", nc, re.I):
            row.nav_contact_label = DEFAULT_CONTACT
        row.save(update_fields=["copyright_text", "nav_contact_label"])

    for slide in HeroSlide.objects.all():
        pl = (slide.primary_label or "").strip()
        changed = False
        if re.search(r"\bbook\b", pl, re.I):
            slide.primary_label = DEFAULT_CONTACT
            slide.primary_url = "#contact"
            changed = True
        sl = (slide.secondary_label or "").strip()
        if re.search(r"\bbook\b", sl, re.I):
            slide.secondary_label = "Our services"
            if not (slide.secondary_url or "").strip():
                slide.secondary_url = "#services"
            changed = True
        if changed:
            slide.save(update_fields=["primary_label", "primary_url", "secondary_label", "secondary_url"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("care", "0017_strip_admin_from_navlinks"),
    ]

    operations = [
        migrations.RunPython(scrub, noop),
    ]
