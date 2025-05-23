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

# Travailler avec l'authentification en local

Le backend d'authentification Agricoll nécessite l'utilisation du protocole HTTPS ainsi que d'URL spécifique (impossible de se connecter depuis localhost par exemple).

Pour faciliter le dévellopement au quotidien il est possible d'utiliser un autre backend OIDC en changeant les variables d'environnement.

Un exemple est donné dans le fichier `.env.dist`, les informations sur les logins et mots de passe, ainsi que les endpoints pour le backend [sont disponibles dans la documentation](https://oidctest.wsweet.org/).

# Travailler avec l'antivirus en local

Les fichiers uploadés sur les documents sont analysé par un antivirus et ne sont pas disponible au téléchargement tant qu'ils n'ont pas été analysé.
En local il est possible de désactiver ce comportement avec la variable d'environnement `BYPASS_ANTIVIRUS` afin d'avoir accès aux fichiers de manière immédiate.

Cette même variable est utilisée dans les tests pour que le fichier soit disponible immédiatement sur l'objet concerné.

Si vous souhaitez réaliser les analyses antivirus en local il faut:
- Vérifier que `BYPASS_ANTIVIRUS` est bien à `False`
- Installer clamav : [instructions pour linux](https://docs.clamav.net/manual/Installing.html#installing-with-a-package-manager) . Attention a bien installer le daemon `clamav-daemon`.
- Lancer la commande `scan_documents` pour analyser les documents et mettre à jour leur statut en base.

# Travailler avec les taches Celery en local

Si vous souhaitez exécuter les taches directement lors de la création sans passer par le broker et le worker
vous pouvez utiliser la variable d'env `CELERY_TASK_ALWAYS_EAGER` à `True`.

Pour travailler avec un broker et Celery en local, il faut:
- Installer un server redis (ou le broker compatible de votre choix)
- Configurer la variable `SCALINGO_REDIS_URL` dans votre fichier `.env`
- Pour lancer les tâches, dans un shell : `celery -A seves worker --loglevel=INFO`
- Pour les tâches de mail les mails sont directement affichés dans la console du worker


# Reconstruire la librairie treeselectJS personalisée

A défaut d'avoir un vrai build côté front pour permettre ce genre de chose:
- Cloner  ` https://github.com/Anto59290/treeselectjs`  (seul le dernier commit est réellement important)
- `npm install` et `npm run build`
- Copier le fichier treeselectjs.umd.js obtenu en sortie de build et le coller dans le projet


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

Tous les commits pour lesquels la CI passe sur main sont automatiquement déployés en recette.

## Django admin
Création d'un super user (commande CLI scalingo à éxecuter en local) :
scalingo --app my-app run python manage.py createsuperuser

# Production

## Mise en production

Scalingo est configuré pour déployer automatiquement tous les commits dont la CI passe qui sont sur la branche production.

Pour le processus plus détaillé de mise en production:

- Merger les PRs qui sont prêtes dans la branche `main`
- Une fois toutes les PR déployées et testées sur la recette, la décision est prise de déployer le lot en cours en production.
- Sur un repo à jour lancer la commande `git log --pretty=format:"%s" origin/production..main` ce qui permet de récupérer le titre des commits qui sont dans `main` mais pas dans `production`.
- Copier le changelog et vérifier que tous les points sont OK.
- Sur Github [créer une nouvelle PR](https://github.com/betagouv/seves/compare/production...main). Vérifiez que la base soit sur `production` et compare sur `main`. Nommer la PR avec comme titre "Mise en production DATE" et ouvrir la PR
- Une fois la CI OK, merger la PR dans la branche `production`
- Le déploiement se fait automatiquement dans Scalingo, suivre que tout se passe bien dans l'interface de Scalingo
- Vérifier que la mise en production s'est bien déroulée
- Annoncer la liste des changements à l'équipe

## CRON
Sur Scalingo, des crons sont configurés via Scalingo Scheduler (cf. fichier cron.json à la racine du projet).
Ils sont monitorés via Sentry Cron Monitors.


## Import du fichier d'extraction des contacts Agricoll
scalingo --app APP_NAME run --file FILE_PATH python manage.py import_contacts /tmp/uploads/FILE_NAME.csv
