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
                "Check: Gmail 2-Step Verification on, App Password (not normal password), "
                "EMAIL_HOST_USER matches that account, port 587 + TLS or 465 + SSL."
            )
            if settings.EMAIL_HOST_USER != recipient and not options["recipient"]:
                self.stderr.write(
                    f"Sending as {settings.EMAIL_HOST_USER}; recipient defaults to the same address."
                )
            raise SystemExit(1) from exc
        self.stdout.write(self.style.SUCCESS(f"Test email sent to {recipient}"))
