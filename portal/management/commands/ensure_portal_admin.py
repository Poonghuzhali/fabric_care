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

        user, created = ensure_portal_admin()
        if options["reset_password"]:
            user.set_password(PORTAL_ADMIN_PASSWORD)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Password reset for {PORTAL_ADMIN_EMAIL}"))
        elif created:
            self.stdout.write(self.style.SUCCESS(f"Created portal admin {PORTAL_ADMIN_EMAIL}"))
        else:
            self.stdout.write(f"Portal admin already exists: {PORTAL_ADMIN_EMAIL}")
