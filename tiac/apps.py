from django.apps import AppConfig


class TiacConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tiac"

    def ready(self):
        import tiac.signals  # noqa: F401
