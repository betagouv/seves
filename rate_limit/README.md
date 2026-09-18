# RATELIMIT

App Django autonome (sans modèle, sans migration) qui :

- compte, via le cache Django, le nombre de pages vues par **utilisateur authentifié** ;
- applique une limite globale de requêtes par heure (fenêtre glissante configurable) ;
- laisse passer les utilisateurs anonymes (le comptage se fait uniquement sur l'utilisateur, jamais sur l'IP) ;
- permet d'exclure des pages ou des groupes de pages (chemins, namespace, nom d'URL) ;
- renvoie un code HTTP dédié (429 par défaut) en cas de dépassement, pour être repérable dans les logs.

Elle ne dépend que de Django et n'importe rien du reste du projet : elle peut être copiée telle quelle dans un
autre paquet/dépôt.

## Installation

```python
INSTALLED_APPS = [
    ...,
    "retelimit",
]

MIDDLEWARE = [
    ...,
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # doit être avant, on a besoin de request.user
    ...,
    "rate_limit.middleware.PageViewRateLimitMiddleware",
]
```
## Réglages (`settings.RATELIMIT`)

Tous optionnels, à regrouper dans un seul dict :

```python
RATELIMIT = {
    "ENABLED": True,
    "MAX_REQUESTS_PER_HOUR": 1000,
    "WINDOW_SECONDS": 3600,
    "EXCLUDED_PATH_PREFIXES": ["/static/", "/media/"],
    "EXCLUDED_URL_NAMES": [],
    "EXCLUDED_NAMESPACES": [],
    "CACHE_ALIAS": "default",
    "CACHE_KEY_PREFIX": "RATELIMIT",
    "STATUS_CODE": 429,
    "RESPONSE_MESSAGE": "Trop de requêtes, veuillez réessayer plus tard.",
}
```

| Clé | Rôle |
| --- | --- |
| `ENABLED` | Coupe-circuit global, sans retirer le middleware. |
| `MAX_REQUESTS_PER_HOUR` | Limite globale, tous types de pages confondus (hors exclusions), par utilisateur et par fenêtre. |
| `WINDOW_SECONDS` | Durée de la fenêtre de comptage (3600s = 1h par défaut). |
| `EXCLUDED_PATH_PREFIXES` | Chemins exclus du comptage *et* du blocage (ex: statique/médias). |
| `EXCLUDED_URL_NAMES` / `EXCLUDED_NAMESPACES` | Exclusion par nom d'URL ou par groupe de pages (namespace d'`include()`). |
| `CACHE_ALIAS` | Backend de `settings.CACHES` utilisé (doit être partagé entre tous les process en prod, donc pas `LocMemCache`). |
| `STATUS_CODE` | Code HTTP renvoyé en cas de dépassement (429 = "Too Many Requests", le code standard pour ça). |
