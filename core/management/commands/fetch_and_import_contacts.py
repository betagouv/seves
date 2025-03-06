import os
import subprocess

from django.core.management import BaseCommand, call_command

from seves import settings


class Command(BaseCommand):
    help = "Récupère et déchiffre les fichiers (export contacts agricoll et clé symétrique) les plus récents depuis le SFTP client puis importe les contacts"

    def get_missing_env_vars(self):
        required_vars = [
            "SFTP_HOST",
            "SFTP_USERNAME",
            "SFTP_PASSWORD",
            "SFTP_PRIVATE_KEY",
            "SFTP_CLEVERCLOUD_KNOWN_HOSTS",
        ]
        return [var for var in required_vars if not os.environ.get(var)]

    def handle(self, *args, **options):
        if missing_env_vars := self.get_missing_env_vars():
            self.stderr.write(f"Erreur: Variables d'environnement manquantes: {', '.join(missing_env_vars)}")
            return
        try:
            subprocess.run(os.path.join(settings.BASE_DIR, "bin", "fetch_contacts_agricoll_and_key.sh"), check=True)
            if not os.path.exists("agricoll.csv"):
                self.stderr.write("Le fichier agricoll.csv n'a pas été créé.")
                return
            call_command("import_contacts", "agricoll.csv")
        except subprocess.CalledProcessError as e:
            self.stderr.write(f"Erreur lors de l'exécution du script : {e}")
