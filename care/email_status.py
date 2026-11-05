from django.conf import settings

from care.brevo_mail import get_brevo_api_key
from care.mail import email_delivery_enabled


def email_config_summary():
    api_key = get_brevo_api_key()
    smtp_user = (getattr(settings, "EMAIL_HOST_USER", "") or "").strip()
    from_email = (getattr(settings, "DEFAULT_FROM_EMAIL", "") or "").strip()
    if api_key:
        method = "brevo_api"
    elif getattr(settings, "EMAIL_CONFIGURED", False):
        method = "smtp"
    else:
        method = "none"
    return {
        "delivery_enabled": email_delivery_enabled(),
        "method": method,
        "brevo_api_configured": bool(api_key),
        "smtp_host": getattr(settings, "EMAIL_HOST", "") or "—",
        "smtp_user": smtp_user or "—",
        "from_email": from_email or "—",
        "from_email_ok": bool(from_email) and not from_email.lower().endswith("@smtp-brevo.com"),
    }
