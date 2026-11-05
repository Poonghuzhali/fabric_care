from django.core.management.base import BaseCommand

from portal.customer_cleanup import purge_all_customers


class Command(BaseCommand):
    help = "Delete all bookings, contact messages, and non-staff customer accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirm deletion without a prompt.",
        )

    def handle(self, *args, **options):
        if not options["yes"]:
            self.stdout.write("This removes ALL bookings, contact messages, and customer logins.")
            self.stdout.write("Staff portal users are kept. Re-run with --yes to proceed.")
            return
        result = purge_all_customers()
        self.stdout.write(
            self.style.SUCCESS(
                f"Removed {result['bookings']} booking(s), {result['messages']} message(s), "
                f"and {result['users']} customer account(s)."
            )
        )
