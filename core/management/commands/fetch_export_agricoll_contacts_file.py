import base64
import datetime
import os
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
import paramiko
from paramiko.client import SSHClient
from paramiko.sftp_attr import SFTPAttributes
from paramiko.sftp_client import SFTPClient


class CleverCloudSftpVerifier(paramiko.MissingHostKeyPolicy):
    """
    Politique de vérification pour les connexions SFTP vers CleverCloud.
    Vérifie à la fois le nom d'hôte et l'empreinte de la clé publique du serveur.
    """

    # Liste des empreintes officielles de CleverCloud
    # https://www.clever-cloud.com/developers/doc/addons/fs-bucket/#from-your-favorite-sftp-client
    CLEVER_CLOUD_FINGERPRINTS = [
        "SHA256:+ku6hhQb1O3OVzkZa2B+htPD+P+5K/X6QQYWXym/4Zo",
        "SHA256:8tZzRvA3Fh9poG7g1bu8m0LQS819UBh7AYcEXJYiPqw",
        "SHA256:HHGCP5cf0jQbQrIRXjiC9aYJGNQ+L9ijOmJUueLp+9A",
        "SHA256:Hyt6ox+v2Lrvdfl29jwe1/dBq9zh2fmq2DO6rqurl7o",
        "SHA256:drShQbl3Ox+sYYYP+urOCtuMiJFh7k1kECdvZ4hMuAE",
        "SHA256:h1oUNRkYaIycchUsyAXPQHnu6MtTF2YUEYuisu+vnOE",
        "SHA256:+550bmBCNAHscjOmKrdweueVUz2E6h1KzmSV+0c0U7w",
        "SHA256:1O7d6cdmqj42Dw4nX90Y+6zIFTUI+aIwD0SLMQuj0ko",
        "SHA256:AkHQnQXJ1lFEtliLHl8hlG7NiIZZgVn/uuRMCZJOKJk",
        "SHA256:Atxhx7U0MOuZC7e4vs1tpyTJmNttB7d4+HNC5hiavFo",
        "SHA256:Bla7GeL6hggg+rf6iDlKMrzIhxEBYB3VL7Q6PYGJYt4",
        "SHA256:H5ZhQ/5JdMPSG49ojUNEhwSuRD663mnIJb/YDFFntyk",
        "SHA256:TZr6eFrzoJmn4RS55Tb6yTd+WV9lTGtW0q+uLVbI7IE",
        "SHA256:ZYFb1AsB+q++NRf7yW8E5rNOfxTRwjpJt6hqFP/NBNs",
        "SHA256:d+nTyowvYtcxF28mCUu1ilqPJuLMExGyJ16Sv/pvoVY",
        "SHA256:flpv4s3VxOrQFc/IG+BpR1s9dgDvR07A6zunNqO4Co0",
        "SHA256:hvZN8rgSG82weLOeMTXdh1VwhjuRv+MJNnUt/X9R39g",
        "SHA256:ls20B8C6Jdqx7RPQAjzVX7KmnrHizJum2sEvNhMcl60",
        "SHA256:u1AzFc2AdFmlPRdNIZsn0sQJ/CKbfC2ZmXnQfabPek4",
        "SHA256:wUPBX3X5gALgxXqD+IwG5qPRb0jbiOZ8/U1BOZeNhtk",
        "SHA256:yRHC/tAlBpHLlRZ5rwbZ1z+159Bj3yg0VxHf+hXINLg",
        "SHA256:yhn79aqxOGQZ+LXdN1/vIY+jwRIbBamlVT1+HdFoA6o",
    ]

    def __init__(self, expected_hostname):
        self.expected_hostname = expected_hostname

    def missing_host_key(self, client, hostname, key):
        if hostname != self.expected_hostname:
            raise paramiko.SSHException("Connexion refusée - host non autorisé")

        if key.fingerprint not in self.CLEVER_CLOUD_FINGERPRINTS:
            raise paramiko.SSHException("Connexion refusée - empreinte de clé non reconnue")


class Command(BaseCommand):
    help = "Récupère et déchiffre les fichiers les plus récents depuis le SFTP client"

    def get_sftp_credentials(self) -> dict[str, str]:
        sftp_host = settings.SFTP_HOST
        sftp_username = settings.SFTP_USERNAME
        sftp_password = settings.SFTP_PASSWORD
        sftp_port = settings.SFTP_PORT

        if not all([sftp_host, sftp_username, sftp_password, sftp_port]):
            raise KeyError(
                "Erreur de configuration SFTP: variables d'environnement SFTP_HOST, SFTP_USERNAME, SFTP_PASSWORD, SFTP_PORT requises"
            )

        return {"hostname": sftp_host, "username": sftp_username, "password": sftp_password, "port": sftp_port}

    def connect_to_sftp(self, credentials: dict[str, str]) -> tuple[SSHClient, SFTPClient]:
        self.stdout.write("Connexion au serveur SFTP...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(CleverCloudSftpVerifier(credentials["hostname"]))
        client.connect(**credentials)
        sftp = client.open_sftp()
        self.stdout.write(self.style.SUCCESS("Connexion SFTP établie"))
        return client, sftp

    def print_files(self, sftp: SFTPClient) -> None:
        self.stdout.write("Liste des fichiers disponibles:")
        for attr in sftp.listdir_attr():
            mod_time = datetime.datetime.fromtimestamp(attr.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.stdout.write(f"- {attr.filename} (Taille: {attr.st_size} octets, Modifié: {mod_time})")

    def find_latest_encrypted_files(self, sftp: SFTPClient) -> tuple[SFTPAttributes, SFTPAttributes]:
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

    def download_files(
        self,
        sftp: SFTPClient,
        encrypted_data_file: SFTPAttributes,
        encrypted_symmetric_key_file: SFTPAttributes,
        base_dir: Path,
    ):
        self.stdout.write(
            f"Téléchargement de {encrypted_data_file.filename} et {encrypted_symmetric_key_file.filename}..."
        )
        encrypted_data_file_path = os.path.join(base_dir, encrypted_data_file.filename)
        encrypted_symmetric_key_file_path = os.path.join(base_dir, encrypted_symmetric_key_file.filename)
        sftp.get(encrypted_data_file.filename, encrypted_data_file_path)
        sftp.get(encrypted_symmetric_key_file.filename, encrypted_symmetric_key_file_path)
        self.stdout.write(self.style.SUCCESS("Fichiers téléchargés"))
        return encrypted_data_file_path, encrypted_symmetric_key_file_path

    def get_private_key_data(self) -> bytes:
        private_key_base64 = os.environ.get("SFTP_PRIVATE_KEY")
        if not private_key_base64:
            raise KeyError("Variable d'environnement SFTP_PRIVATE_KEY requise")
        return base64.b64decode(private_key_base64)

    def decrypt_symmetric_key(self, private_key_data: bytes, encrypted_symmetric_key_file_path: str, base_dir: Path):
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

    def decrypt_data_file(self, encrypt_data_file_path: str, symmetric_key_path: str, base_dir: Path):
        self.stdout.write("Déchiffrement du fichier de données...")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        decrypted_file_path = os.path.join(
            base_dir, f"{timestamp}_{os.path.basename(encrypt_data_file_path).replace('.encrypted', '')}"
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
                    encrypt_data_file_path,
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
            decrypted_file_path = self.decrypt_data_file(
                encrypt_data_file_path, symmetric_key_file_path, settings.BASE_DIR
            )
            os.remove(encrypted_symmetric_key_file_path)
            os.remove(symmetric_key_file_path)
            os.remove(encrypt_data_file_path)
            call_command("import_contacts", decrypted_file_path)
            os.remove(decrypted_file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur : {str(e)}"))
        finally:
            self.close_sftp_connection(sftp, client)
