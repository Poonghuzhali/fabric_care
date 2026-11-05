from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "portal"
    verbose_name = "Service portal"

    def ready(self):
        from django.db.models.signals import post_migrate

        from portal.accounts import ensure_portal_admin

        def _bootstrap(sender, **kwargs):
            if sender.name != self.name:
                return
            ensure_portal_admin()

        post_migrate.connect(_bootstrap, sender=self)
