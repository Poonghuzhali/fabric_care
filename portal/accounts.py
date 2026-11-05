from django.contrib.auth import get_user_model

PORTAL_ADMIN_EMAIL = "admin@serviceportal.com"
PORTAL_ADMIN_PASSWORD = "AdminSecure#2026"


def ensure_portal_admin(**kwargs):
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
    if created:
        user.set_password(PORTAL_ADMIN_PASSWORD)
    user.save()
    return user, created or changed
