import os

from django.contrib.auth import get_user_model

PORTAL_ADMIN_EMAIL = "admin@serviceportal.com"
PORTAL_ADMIN_PASSWORD = "AdminSecure#2026"


def ensure_portal_admin(*, reset_password=False):
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=PORTAL_ADMIN_EMAIL,
        defaults={
            "email": PORTAL_ADMIN_EMAIL,
            "is_staff": True,
            "is_superuser": True,
            "first_name": "Portal",
            "last_name": "Admin",
        },
    )
    changed = created
    if not user.is_staff:
        user.is_staff = True
        changed = True
    if not user.is_superuser:
        user.is_superuser = True
        changed = True
    if user.email != PORTAL_ADMIN_EMAIL:
        user.email = PORTAL_ADMIN_EMAIL
        changed = True
    sync_password = reset_password or created or not user.has_usable_password()
    if not sync_password and os.environ.get("PORTAL_ADMIN_SYNC_PASSWORD", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        sync_password = True
    if sync_password:
        user.set_password(PORTAL_ADMIN_PASSWORD)
        changed = True
    user.save()
    return user, created or changed
