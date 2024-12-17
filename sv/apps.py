from django.apps import AppConfig


class SvConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sv"

    def ready(self):
        import sv.signals  # noqa: F401
