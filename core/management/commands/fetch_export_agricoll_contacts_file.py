import base64
import datetime
import os
import subprocess
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand
import paramiko


class Command(BaseCommand):
    help = "Récupère et déchiffre les fichiers les plus récents depuis le SFTP client"

    def get_sftp_credentials(self):
        sftp_host = settings.SFTP_HOST
        sftp_username = settings.SFTP_USERNAME
        sftp_password = settings.SFTP_PASSWORD
        sftp_port = settings.SFTP_PORT

        if not all([sftp_host, sftp_username, sftp_password, sftp_port]):
            raise KeyError(
                "Erreur de configuration SFTP: variables d'environnement SFTP_HOST, SFTP_USERNAME, SFTP_PASSWORD, SFTP_PORT requises"
            )

        return {"hostname": sftp_host, "username": sftp_username, "password": sftp_password, "port": sftp_port}

    def connect_to_sftp(self, credentials):
        self.stdout.write("Connexion au serveur SFTP...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # TODO: Ajouter une vérification de l'hôte
        client.connect(**credentials)
        sftp = client.open_sftp()
        self.stdout.write(self.style.SUCCESS("Connexion SFTP établie"))
        return client, sftp

    def print_files(self, sftp):
        self.stdout.write("Liste des fichiers disponibles:")
        for attr in sftp.listdir_attr():
            mod_time = datetime.datetime.fromtimestamp(attr.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.stdout.write(f"- {attr.filename} (Taille: {attr.st_size} octets, Modifié: {mod_time})")

    def find_latest_encrypted_files(self, sftp):
        """Trouve les fichiers chiffrés (fichier de données et la clé symétrique) les plus récents sur le serveur SFTP"""
        file_list = sftp.listdir_attr()

        if not file_list:
            raise FileNotFoundError("Aucun fichier trouvé sur le serveur SFTP")

        latest_data_file = None
        latest_encrypted_symmetric_key_file = None
        for attr in file_list:
            if attr.filename.endswith(".encrypted") and not attr.filename.endswith(".key.encrypted"):
                if latest_data_file is None or attr.st_mtime > latest_data_file.st_mtime:
                    latest_data_file = attr
            elif attr.filename.endswith(".key.encrypted"):
                if (
                    latest_encrypted_symmetric_key_file is None
                    or attr.st_mtime > latest_encrypted_symmetric_key_file.st_mtime
                ):
                    latest_encrypted_symmetric_key_file = attr

        if not latest_data_file:
            raise FileNotFoundError("Aucun fichier de données chiffré (.encrypted) trouvé sur le serveur SFTP")
        if not latest_encrypted_symmetric_key_file:
            raise FileNotFoundError("Aucune clé symétrique chiffrée (.key.encrypted) trouvé sur le serveur SFTP")

        return latest_data_file, latest_encrypted_symmetric_key_file

    def download_files(self, sftp, encrypted_data_file, encrypted_symmetric_key_file, base_dir):
        self.stdout.write(
            f"Téléchargement de {encrypted_data_file.filename} et {encrypted_symmetric_key_file.filename}..."
        )
        data_file_path = os.path.join(base_dir, encrypted_data_file.filename)
        symmetric_key_file_path = os.path.join(base_dir, encrypted_symmetric_key_file.filename)
        sftp.get(encrypted_data_file.filename, data_file_path)
        sftp.get(encrypted_symmetric_key_file.filename, symmetric_key_file_path)
        self.stdout.write(self.style.SUCCESS("Fichiers téléchargés"))
        return data_file_path, symmetric_key_file_path

    def get_private_key_data(self):
        private_key_base64 = os.environ.get("SFTP_PRIVATE_KEY")
        if not private_key_base64:
            raise KeyError("Variable d'environnement SFTP_PRIVATE_KEY requise")
        return base64.b64decode(private_key_base64)

    def decrypt_symmetric_key(self, private_key_data, encrypted_symmetric_key_file_path, base_dir):
        self.stdout.write("Déchiffrement de la clé symétrique...")
        with tempfile.NamedTemporaryFile() as temp_key_file_private_key:
            temp_key_file_private_key.write(private_key_data)
            temp_key_file_private_key.flush()
            symmetric_key_file_path = os.path.join(base_dir, "symmetric.key")
            try:
                subprocess.run(
                    [
                        "openssl",
                        "rsautl",
                        "-decrypt",
                        "-inkey",
                        temp_key_file_private_key.name,
                        "-in",
                        encrypted_symmetric_key_file_path,
                        "-out",
                        symmetric_key_file_path,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Erreur lors du déchiffrement de la clé symétrique: {str(e)}")

        self.stdout.write(self.style.SUCCESS("Clé symétrique déchiffrée"))
        return symmetric_key_file_path

    def decrypt_data_file(self, data_file_path, symmetric_key_path, base_dir):
        self.stdout.write("Déchiffrement du fichier de données...")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        decrypted_file_path = os.path.join(
            base_dir, f"{timestamp}_{os.path.basename(data_file_path).replace('.encrypted', '')}"
        )
        try:
            subprocess.run(
                [
                    "openssl",
                    "enc",
                    "-d",
                    "-aes-256-cbc",
                    "-a",
                    "-salt",
                    "-pbkdf2",
                    "-in",
                    data_file_path,
                    "-out",
                    decrypted_file_path,
                    "-pass",
                    f"file:{symmetric_key_path}",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erreur lors du déchiffrement du fichier de données: {str(e)}")
        self.stdout.write(self.style.SUCCESS(f"Fichier déchiffré: {decrypted_file_path}"))
        return decrypted_file_path

    def close_sftp_connection(self, sftp, client):
        if sftp:
            sftp.close()
        if client:
            client.close()
        self.stdout.write(self.style.SUCCESS("Connexion SFTP fermée"))

    def handle(self, *args, **options):
        client, sftp = None, None
        try:
            credentials = self.get_sftp_credentials()
            client, sftp = self.connect_to_sftp(credentials)
            self.print_files(sftp)
            latest_encrypted_data_file, latest_encrypted_symmetric_key_file = self.find_latest_encrypted_files(sftp)
            encrypt_data_file_path, encrypted_symmetric_key_file_path = self.download_files(
                sftp, latest_encrypted_data_file, latest_encrypted_symmetric_key_file, settings.BASE_DIR
            )
            private_key_data = self.get_private_key_data()
            symmetric_key_file_path = self.decrypt_symmetric_key(
                private_key_data, encrypted_symmetric_key_file_path, settings.BASE_DIR
            )
            self.decrypt_data_file(encrypt_data_file_path, symmetric_key_file_path, settings.BASE_DIR)
            os.remove(encrypted_symmetric_key_file_path)
            os.remove(symmetric_key_file_path)
            os.remove(encrypt_data_file_path)
            # TODO: remove le fichier de données déchiffré après utilisation
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f"{str(e)}"))
        except FileNotFoundError as e:
            self.stdout.write(self.style.WARNING(f"{str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur : {str(e)}"))
        finally:
            self.close_sftp_connection(sftp, client)
