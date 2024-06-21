# Sèves
Gestion mutualisée de tous les événements sanitaires

- [Technologies](#technologies)
- [Installation et configuration](#installation-et-configuration)
  - [Récupération du code source](#récupération-du-code-source)
  - [Python 3](#python-3)
  - [Création de l'environnement virtuel Python](#création-de-lenvironnement-virtuel-python)
  - [Activation de l'environnement virtuel Python](#activation-de-lenvironnement-virtuel-python)
  - [Installation de pip-tools](#installation-de-pip-tools)
  - [Installation des dépendances Python](#installation-des-dépendances-python)
  - [Création de la base de données](#création-de-la-base-de-données)
  - [Variables d'environnement](#variables-denvironnement)
  - [Initialisation de la base de données](#initialisation-de-la-base-de-données)
  - [Creation d'un super utilisateur pour l'accès à Django Admin](#creation-dun-super-utilisateur-pour-laccès-à-django-admin)
  - [Démarrer le serveur de développement](#démarrer-le-serveur-de-développement)
- [Gestion des dépendances Python](#gestion-des-dépendances-python)
- [Tests](#tests)
  - [E2E](#e2e)
- [Recette](#recette)
  - [Déploiement](#déploiement)
  - [Django admin](#django-admin)
- [Production](#production)
- [CRON](#cron)

# Technologies
- Git
- PostgreSQL
- Python 3
- Django
- HTML, CSS
- Système de Design de l'État [DSFR](https://www.systeme-de-design.gouv.fr/)
- JavaScript (AlpineJS, vanilla)
- Pytest
- Playwright (tests E2E)
- Ruff (linter/formatter)
- Pre-commit
- DjHTML (indenter)
- Sentry

# Installation et configuration
## Récupération du code source
```
git clone git@github.com:betagouv/seves.git
```

## Python 3
Assurez vous d'avoir [Python 3](https://www.python.org/downloads/) d'installé.

## Création de l'environnement virtuel Python
```
python3 -m venv venv
```
## Activation de l'environnement virtuel Python
```
source venv/bin/activate
```
## Installation de pip-tools
```
pip install pip-tools
```
## Installation des dépendances Python
```
pip-sync
```

## Création de la base de données
Créez la base de données via un client PosgreSQL ou la ligne de commande `psql` (exemple: `seves`).

## Variables d'environnement
Copiez le fichier d'exemple fourni (`.env.dist`) et définissez les variables d'environnement :
```
cp .env.dist .env
```

## Initialisation de la base de données
```
./manage.py migrate
```

## Creation d'un super utilisateur pour l'accès à Django Admin
```
./manage.py createsuperuser
```

## Démarrer le serveur de développement
```
./manage.py runserver
```
Se rendre sur http://localhost:8000/

# Gestion des dépendances Python
Les dépendances sont gérées via [pip-tools](https://github.com/jazzband/pip-tools).

Pour ajouter une nouvelle dépendance au projet :
- ajoutez la dépendance dans le fichier requirements.in
- executez la commande `pip-compile` (pour mettre à à jour le fichier `requirements.txt`)
- executez la commande `pip-sync` (installation de la nouvelle dépendance)

# Travailler avec un service S3 local

Suivre [la documentation de minio](https://hub.docker.com/r/minio/minio) sur le hub docker, en résumé pour avoir le stockage persistent:

```bash
sudo mkdir /mnt/data
sudo chown votre_user:votre_groupe /mnt/data/
podman run -v /mnt/data:/data  -p 9000:9000 -p 9001:9001 quay.io/minio/minio server /data --console-address ":9001"
```

Une fois dans la console Web de minio vous pouvez vous créer une clé d'accès ainsi qu'un bucket en local.
Configurez ensuite votre fichier .env avec `STORAGE_ENGINE="storages.backends.s3.S3Storage"` et les tokens d'authentification (cf exemple dans .env.dist).

# Tests
## E2E
Les tests E2E sont réalisés avec la bibliothèque [Playwright](https://playwright.dev/python/) ([installé précédemment](#Installation-des-dépendances-Python)).

Avant de pouvoir lancer les tests E2E, il faut installer les navigateurs ([source](https://playwright.dev/python/docs/intro#installing-playwright-pytest)) :
```
playwright install
```
Lancez les tests :
```
python -m pytest
```

# Recette
## Déploiement
git push scalingo main
## Django admin
Création d'un super user (commande CLI scalingo à éxecuter en local) :
scalingo --app my-app run python manage.py createsuperuser

# Production



# CRON
Sur Scalingo, des crons sont configurés via Scalingo Scheduler (cf. fichier cron.json à la racine du projet).
Ils sont monitorés via Sentry Cron Monitors.


# Import du fichier d'extraction des contacts Agricoll
scalingo --app APP_NAME run --file FILE_PATH python manage.py import_contacts /tmp/uploads/FILE_NAME.csv
