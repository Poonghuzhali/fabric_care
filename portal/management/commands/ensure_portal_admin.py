from django.core.management.base import BaseCommand

from portal.accounts import PORTAL_ADMIN_EMAIL, ensure_portal_admin


class Command(BaseCommand):
    help = "Create or update the preset service portal admin account."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Reset the portal password to the preset value.",
        )

    def handle(self, *args, **options):
        from portal.accounts import PORTAL_ADMIN_PASSWORD
        from django.contrib.auth import get_user_model

        user, changed = ensure_portal_admin(reset_password=options["reset_password"])
        if options["reset_password"]:
            self.stdout.write(self.style.SUCCESS(f"Password reset for {PORTAL_ADMIN_EMAIL}"))
        elif changed and user.date_joined:
            self.stdout.write(self.style.SUCCESS(f"Portal admin ready: {PORTAL_ADMIN_EMAIL}"))
        else:
            self.stdout.write(f"Portal admin already exists: {PORTAL_ADMIN_EMAIL}")
