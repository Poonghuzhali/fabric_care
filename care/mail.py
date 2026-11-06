import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from care.brevo_mail import get_brevo_api_key, send_transactional_email

logger = logging.getLogger(__name__)


def email_delivery_enabled():
    """True when mail will leave the app (Brevo API, SMTP, or test locmem)."""
    if get_brevo_api_key():
        return True
    backend = (settings.EMAIL_BACKEND or "").lower()
    if "console" in backend:
        return False
    if "locmem" in backend:
        return True
    return bool(getattr(settings, "EMAIL_CONFIGURED", False)) and "smtp" in backend


def _smtp_from_email(site=None):
    """
    From address must be a verified sender (DEFAULT_FROM_EMAIL).
    Brevo SMTP login (*@smtp-brevo.com) is used only for authentication, not as From.
    """
    from_email = (settings.DEFAULT_FROM_EMAIL or "").strip()
    smtp_user = (settings.EMAIL_HOST_USER or "").strip()
    if not from_email or from_email.lower() == smtp_user.lower():
        if smtp_user.lower().endswith("@smtp-brevo.com"):
            from_email = (site.email if site and site.email else "hello@vastracare.in").strip()
        else:
            from_email = smtp_user or from_email
    reply_to = []
    if site and site.email:
        studio = site.email.strip()
        if studio and studio.lower() != str(from_email).lower():
            reply_to = [studio]
    return from_email, reply_to


def send_contact_enquiry_notification(*, message_obj, site=None):
    """Notify the business when someone submits the public contact form."""
    if not email_delivery_enabled():
        logger.warning("Contact form saved (#%s) but email is not configured.", message_obj.pk)
        return
    to_email = ""
    if site:
        to_email = (site.enquiry_inbox_email or site.email or "").strip()
    if not to_email:
        to_email = getattr(settings, "CONTACT_ENQUIRY_EMAIL", "").strip()
    if not to_email:
        logger.warning("Contact form #%s saved but no enquiry inbox email configured.", message_obj.pk)
        return

    brand = site.brand_name if site and site.brand_name else "Vastra Care"
    from_email, _reply_to = _smtp_from_email(site)
    subject = f"{brand} — enquiry from {message_obj.name}"
    text_body = (
        f"Name: {message_obj.name}\n"
        f"Email: {message_obj.email}\n"
        f"Phone: {message_obj.phone or '—'}\n\n"
        f"{message_obj.message}\n"
    )
    html_body = (
        f"<p><strong>Name:</strong> {message_obj.name}<br>"
        f"<strong>Email:</strong> {message_obj.email}<br>"
        f"<strong>Phone:</strong> {message_obj.phone or '—'}</p>"
        f"<p>{message_obj.message.replace(chr(10), '<br>')}</p>"
    )
    if get_brevo_api_key():
        send_transactional_email(
            sender_email=from_email,
            sender_name=brand,
            to_email=to_email,
            to_name=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
        logger.info("Contact enquiry notification sent via Brevo to %s", to_email)
        return
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[to_email],
        reply_to=[message_obj.email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)
    logger.info("Contact enquiry notification sent to %s", to_email)


def send_test_email_message(*, recipient, site=None):
    """Send a plain test message using the same Brevo API / SMTP path as contact mail."""
    if not email_delivery_enabled():
        raise RuntimeError("Email is not configured on this server.")
    from_email, _reply_to = _smtp_from_email(site)
    brand = site.brand_name if site and site.brand_name else "Vastra Care"
    subject = f"{brand} — test email"
    text_body = "If you received this, outbound email is configured correctly."
    if get_brevo_api_key():
        send_transactional_email(
            sender_email=from_email,
            sender_name=brand,
            to_email=recipient,
            to_name=recipient,
            subject=subject,
            text_body=text_body,
            html_body=f"<p>{text_body}</p>",
        )
        return
    from django.core.mail import send_mail

    send_mail(
        subject=subject,
        message=text_body,
        from_email=from_email,
        recipient_list=[recipient],
        fail_silently=False,
    )
