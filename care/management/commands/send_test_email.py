from django.conf import settings
from django.core.management.base import BaseCommand

from care.mail import email_delivery_enabled, send_test_email_message
from care.models import SiteSetting


class Command(BaseCommand):
    help = "Send a test email using current SMTP / .env settings."

    def add_arguments(self, parser):
        parser.add_argument(
            "recipient",
            nargs="?",
            default="",
            help="Recipient email (defaults to EMAIL_HOST_USER).",
        )

    def handle(self, *args, **options):
        recipient = (options["recipient"] or settings.EMAIL_HOST_USER or "").strip()
        if not recipient:
            self.stderr.write(
                "Set EMAIL_HOST_USER in .env or pass a recipient: "
                "python manage.py send_test_email you@example.com"
            )
            return
        if not email_delivery_enabled():
            self.stderr.write("Email is not configured. Check BREVO_API_KEY or SMTP env vars.")
            return
        try:
            send_test_email_message(recipient=recipient, site=SiteSetting.objects.first())
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"SMTP failed: {exc}"))
            self.stderr.write(
                "Check Brevo: BREVO_API_KEY (xkeysib-…) OR SMTP (smtp-relay.brevo.com, "
                "EMAIL_HOST_USER=c1a0e2001@smtp-brevo.com, BREVO_SMTP_KEY=SMTP password). "
                "DEFAULT_FROM_EMAIL must be a verified sender. "
                "If IP allowlisting is on in Brevo, disable it or Render mail will fail."
            )
            if settings.EMAIL_HOST_USER != recipient and not options["recipient"]:
                self.stderr.write(
                    f"Sending as {settings.EMAIL_HOST_USER}; recipient defaults to the same address."
                )
            raise SystemExit(1) from exc
        self.stdout.write(self.style.SUCCESS(f"Test email sent to {recipient}"))
