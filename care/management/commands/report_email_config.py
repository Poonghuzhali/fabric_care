from django.core.management.base import BaseCommand

from care.email_status import email_config_summary


class Command(BaseCommand):
    help = "Print email configuration status (shown in Render build logs; no secrets)."

    def handle(self, *args, **options):
        info = email_config_summary()
        self.stdout.write("--- Email configuration (Render build) ---")
        self.stdout.write(f"Delivery enabled: {info['delivery_enabled']}")
        self.stdout.write(f"Method: {info['method']}")
        self.stdout.write(f"Brevo API key set: {info['brevo_api_configured']}")
        self.stdout.write(f"SMTP host: {info['smtp_host']}")
        self.stdout.write(f"SMTP login: {info['smtp_user']}")
        self.stdout.write(f"From address: {info['from_email']}")
        if not info["from_email_ok"]:
            self.stdout.write(
                self.style.WARNING(
                    "DEFAULT_FROM_EMAIL must be a verified sender (not @smtp-brevo.com)."
                )
            )
        if not info["delivery_enabled"]:
            self.stdout.write(
                self.style.WARNING(
                    "Set BREVO_API_KEY (xkeysib-…) or BREVO_SMTP_KEY + EMAIL_HOST_USER on Render."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("Email ready for contact form notifications."))
