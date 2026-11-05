from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


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
        if not settings.EMAIL_HOST:
            self.stderr.write("EMAIL_HOST is not configured. Check your .env file.")
            return
        try:
            send_mail(
                subject="Vastra Care — SMTP test",
                message="If you received this, booking confirmation email is configured correctly.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"SMTP failed: {exc}"))
            self.stderr.write(
                "Check Brevo: EMAIL_HOST=smtp-relay.brevo.com, port 587 + TLS, "
                "EMAIL_HOST_USER = SMTP login email from Brevo dashboard, "
                "EMAIL_HOST_PASSWORD or BREVO_SMTP_KEY = your SMTP key (not API key), "
                "DEFAULT_FROM_EMAIL = a verified sender in Brevo."
            )
            if settings.EMAIL_HOST_USER != recipient and not options["recipient"]:
                self.stderr.write(
                    f"Sending as {settings.EMAIL_HOST_USER}; recipient defaults to the same address."
                )
            raise SystemExit(1) from exc
        self.stdout.write(self.style.SUCCESS(f"Test email sent to {recipient}"))
