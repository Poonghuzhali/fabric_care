import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from care.templatetags.care_tags import format_inr

logger = logging.getLogger(__name__)


def email_delivery_enabled():
    """True when mail will leave the app (SMTP or test locmem), not console-only."""
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


def send_booking_confirmation(booking, site=None):
    """Send order confirmation to the customer's email."""
    if not email_delivery_enabled():
        raise RuntimeError("SMTP is not configured; cannot send booking confirmation email.")
    price = ""
    if booking.service_id:
        service = booking.service
        if service is None:
            from care.models import Service

            service = Service.objects.filter(pk=booking.service_id).first()
        if service:
            price = format_inr(service.price)

    site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    context = {
        "booking": booking,
        "site": site,
        "site_url": site_url,
        "price": price,
        "brand": site.brand_name if site and site.brand_name else "Vastra Care",
    }
    subject = render_to_string("emails/booking_confirmation_subject.txt", context).strip()
    text_body = render_to_string("emails/booking_confirmation.txt", context)
    html_body = render_to_string("emails/booking_confirmation.html", context)

    from_email, reply_to = _smtp_from_email(site)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[booking.email],
        reply_to=reply_to or None,
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)
    logger.info("Booking confirmation email sent to %s (booking #%s)", booking.email, booking.pk)
