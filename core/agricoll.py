import base64
import logging
import os
import subprocess
import tempfile

from django.conf import settings
import paramiko
from paramiko.client import SSHClient, MissingHostKeyPolicy
from paramiko.sftp_client import SFTPClient


class CleverCloudSftpVerifier(MissingHostKeyPolicy):
    """
    Politique de vérification pour les connexions SFTP vers CleverCloud.
    Vérifie à la fois le nom d'hôte et l'empreinte de la clé publique du serveur.
    """

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
    EXPECTED_HOSTNAME = settings.SFTP_HOST

    def missing_host_key(self, client, hostname, key):
        if hostname != self.EXPECTED_HOSTNAME:
            raise paramiko.SSHException("Connexion refusée - host non autorisé")
        if key.fingerprint not in self.CLEVER_CLOUD_FINGERPRINTS:
            raise paramiko.SSHException("Connexion refusée - empreinte de clé non reconnue")


class SftpAgricoll:
    ENCRYPTED_DATA_FILE_SUFFIX = ".encrypted"
    ENCRYPTED_SYMMETRIC_KEY_FILE_SUFFIX = ".key.encrypted"
    SFTP_REMOTE_DIRECTORY = "."

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client: SSHClient | None = None
        self.sftp: SFTPClient | None = None
        self.encrypted_data_file_path: str = os.path.join(settings.BASE_DIR, "contacts_agricoll.csv.encrypted")
        self.encrypted_symmetric_key_file_path: str = os.path.join(settings.BASE_DIR, "symmetric.key.encrypted")
        self.data_file_path = os.path.join(settings.BASE_DIR, "contacts_agricoll.csv")
        self.symmetric_key_file_path: str = os.path.join(settings.BASE_DIR, "symmetric.key")

    def connect_to_sftp(self):
        self.logger.info("Connexion au serveur SFTP...")
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(CleverCloudSftpVerifier())
        self.client.connect(
            hostname=settings.SFTP_HOST,
            username=settings.SFTP_USERNAME,
            password=settings.SFTP_PASSWORD,
            port=settings.SFTP_PORT,
        )
        self.sftp = self.client.open_sftp()
        self.logger.info("Connexion SFTP établie")

    def download_latest_encrypted_data_file(self):
        """Trouve et télécharge le fichier de données chiffré (.encrypted) le plus récent sur le serveur SFTP."""
        file_list = self.sftp.listdir_attr(self.SFTP_REMOTE_DIRECTORY)
        encrypted_data_files = [
            f
            for f in file_list
            if f.filename.endswith(self.ENCRYPTED_DATA_FILE_SUFFIX)
            and not f.filename.endswith(self.ENCRYPTED_SYMMETRIC_KEY_FILE_SUFFIX)
        ]
        try:
            latest_encrypted_data_filename = max(encrypted_data_files, key=lambda f: f.st_mtime).filename
            self.logger.info(f"Téléchargement de {latest_encrypted_data_filename}...")
            self.sftp.get(
                f"{self.SFTP_REMOTE_DIRECTORY}/{latest_encrypted_data_filename}", self.encrypted_data_file_path
            )
            self.logger.info("Fichier téléchargé")
        except ValueError:
            raise FileNotFoundError(
                f"Aucun fichier de données chiffré ({self.ENCRYPTED_DATA_FILE_SUFFIX}) trouvé sur le serveur SFTP"
            )

    def download_latest_encrypted_symmetric_key_file(self):
        """Trouve et télécharge la clé symétrique chiffrée (.key.encrypted) la plus récente sur le serveur SFTP."""
        file_list = self.sftp.listdir_attr(self.SFTP_REMOTE_DIRECTORY)
        encrypted_key_files = [f for f in file_list if f.filename.endswith(self.ENCRYPTED_SYMMETRIC_KEY_FILE_SUFFIX)]
        try:
            latest_encrypted_symmetric_key_filename = max(encrypted_key_files, key=lambda f: f.st_mtime).filename
            self.logger.info(f"Téléchargement de {latest_encrypted_symmetric_key_filename}...")
            self.sftp.get(
                f"{self.SFTP_REMOTE_DIRECTORY}/{latest_encrypted_symmetric_key_filename}",
                self.encrypted_symmetric_key_file_path,
            )
            self.logger.info("Fichier téléchargé")
        except ValueError:
            raise FileNotFoundError(
                f"Aucune clé symétrique chiffrée ({self.ENCRYPTED_SYMMETRIC_KEY_FILE_SUFFIX}) trouvée sur le serveur SFTP"
            )

    def _get_private_key_content(self) -> bytes:
        private_key_base64 = os.environ.get("SFTP_PRIVATE_KEY")
        if not private_key_base64:
            raise KeyError("Variable d'environnement SFTP_PRIVATE_KEY requise")
        return base64.b64decode(private_key_base64)

    def decrypt_symmetric_key(self):
        self.logger.info("Déchiffrement de la clé symétrique...")
        with tempfile.NamedTemporaryFile() as temp_private_key_file:
            temp_private_key_file.write(self._get_private_key_content())
            temp_private_key_file.flush()
            try:
                subprocess.run(
                    [
                        "openssl",
                        "pkeyutl",
                        "-decrypt",
                        "-inkey",
                        temp_private_key_file.name,
                        "-in",
                        self.encrypted_symmetric_key_file_path,
                        "-out",
                        self.symmetric_key_file_path,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Erreur lors du déchiffrement de la clé symétrique: {str(e)}")
        self.logger.info("Clé symétrique déchiffrée")

    def decrypt_data_file(self):
        self.logger.info("Déchiffrement du fichier de données...")
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
                    self.encrypted_data_file_path,
                    "-out",
                    self.data_file_path,
                    "-pass",
                    f"file:{self.symmetric_key_file_path}",
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erreur lors du déchiffrement du fichier de données: {str(e)}")
        self.logger.info("Fichier de données déchiffré")
        return self.data_file_path

    def clean_files(self):
        self.logger.info("Suppression des fichiers locaux...")
        os.remove(self.encrypted_symmetric_key_file_path)
        os.remove(self.symmetric_key_file_path)
        os.remove(self.encrypted_data_file_path)
        os.remove(self.data_file_path)
        self.logger.info("Fichiers locaux supprimés")

    def close_connections(self):
        self.sftp.close()
        self.client.close()
