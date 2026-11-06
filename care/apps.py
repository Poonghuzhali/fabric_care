from django.apps import AppConfig


class CareConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "care"
    verbose_name = "Landing page"

    def ready(self):
        import logging

        from django.conf import settings

        if settings.EMAIL_HOST and not getattr(settings, "EMAIL_CONFIGURED", True):
            logging.getLogger(__name__).warning(
                "Outbound email: update .env with your SMTP or Brevo settings "
                "(see .env.example). Contact form notifications may fail until configured."
            )
