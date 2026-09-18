from django.apps import AppConfig


class RatelimitConfig(AppConfig):
    name = "rate_limit"
    verbose_name = "Comptage des pages vues et limitation de débit par utilisateur"
