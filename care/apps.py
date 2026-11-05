from django.apps import AppConfig


class CareConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "care"
    verbose_name = "Landing page"

    def ready(self):
        import logging

        from django.conf import settings
        from django.contrib import admin

        admin.site.site_header = "Iron Me·Ka"
        admin.site.site_title = "Iron Me·Ka Admin"
        admin.site.index_title = "Manage every section of the landing page"

        if settings.EMAIL_HOST and not getattr(settings, "EMAIL_CONFIGURED", True):
            logging.getLogger(__name__).warning(
                "Booking confirmation email: update .env with your real Gmail and app password "
                "(see .env.example). Until then, SMTP may fail after each booking."
            )
        if getattr(settings, "RAZORPAY_KEY_ID", "") and not getattr(settings, "RAZORPAY_KEY_SECRET", ""):
            logging.getLogger(__name__).warning(
                "Razorpay: RAZORPAY_KEY_ID is set but RAZORPAY_KEY_SECRET is missing in .env — "
                "Pay & request booking will not work until both are set (Test mode keys)."
            )
