import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def get_brevo_api_key():
    """Brevo REST API key (xkeysib-…). Not the same as the SMTP relay password."""
    explicit = getattr(settings, "BREVO_API_KEY", "") or ""
    if explicit:
        return explicit.strip()
    for candidate in (
        getattr(settings, "BREVO_SMTP_KEY", ""),
        getattr(settings, "EMAIL_HOST_PASSWORD", ""),
    ):
        value = (candidate or "").strip()
        if value.startswith("xkeysib-"):
            return value
    return ""


def send_transactional_email(*, sender_email, sender_name, to_email, to_name, subject, text_body, html_body):
    api_key = get_brevo_api_key()
    if not api_key:
        raise RuntimeError("BREVO_API_KEY is not configured.")
    payload = {
        "sender": {"name": sender_name or "Vastra Care", "email": sender_email},
        "to": [{"email": to_email, "name": to_name or to_email}],
        "subject": subject,
        "htmlContent": html_body,
        "textContent": text_body,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        BREVO_API_URL,
        data=data,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=getattr(settings, "EMAIL_TIMEOUT", 30)) as response:
            if response.status not in (200, 201):
                body = response.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"Brevo API returned {response.status}: {body[:500]}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        logger.exception("Brevo API HTTP error %s: %s", exc.code, detail[:500])
        raise RuntimeError(f"Brevo API error {exc.code}: {detail[:300]}") from exc
    logger.info("Brevo API email queued to %s", to_email)
