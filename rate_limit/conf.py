from django.conf import settings

DEFAULTS = {
    # Coupe-circuit global, sans avoir à retirer le middleware.
    "ENABLED": True,
    # Nombre de pages vues autorisées par utilisateur sur la fenêtre glissante ci-dessous.
    "MAX_REQUESTS_PER_HOUR": 100,
    # Durée de la fenêtre de comptage, en secondes (1h par défaut).
    "WINDOW_SECONDS": 3600,
    # Préfixes de chemin exclus du comptage et du rate limiting (ex: fichiers statiques/médias).
    "EXCLUDED_PATH_PREFIXES": ["/static/", "/media/"],
    # Noms d'URL (`url_name`) exclus.
    "EXCLUDED_URL_NAMES": [],
    # Namespaces d'URL (`app_name`) exclus, pour exclure un groupe de pages entier.
    "EXCLUDED_NAMESPACES": [],
    # Alias du cache Django (settings.CACHES) à utiliser pour le comptage.
    "CACHE_ALIAS": "default",
    # Préfixe des clés de cache utilisées
    "CACHE_KEY_PREFIX": "ratelimit",
    # Code HTTP dédié renvoyé lorsqu'un utilisateur dépasse la limite.
    "STATUS_CODE": 429,
    # Corps de la réponse renvoyée lorsqu'un utilisateur dépasse la limite.
    "RESPONSE_MESSAGE": "Trop de requêtes, veuillez réessayer plus tard.",
}


class AppSettings:
    """Lit `settings.RATELIMIT` à chaque accès (compatible avec `override_settings` dans les tests)."""

    def __getattr__(self, name):
        if name not in DEFAULTS:
            raise AttributeError(f"Réglage inconnu pour RATELIMIT: {name}")
        user_settings = getattr(settings, "RATELIMIT", {})
        return user_settings.get(name, DEFAULTS[name])


app_settings = AppSettings()
