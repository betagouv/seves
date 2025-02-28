import paramiko
from django.core.management import call_command
from testcontainers.sftp import SFTPContainer

from core.management.commands.fetch_export_agricoll_contacts_file import CleverCloudSftpVerifier


def test_fetch_export_agricoll_contacts_command(settings):
    with SFTPContainer() as sftp_container:
        # Surcharge des paramètres de configuration avec le container SFTP
        settings.SFTP_HOST = sftp_container.get_container_host_ip()
        settings.SFTP_PORT = sftp_container.get_exposed_sftp_port()
        settings.SFTP_USERNAME = sftp_container.users[0].name
        settings.SFTP_PASSWORD = sftp_container.users[0].password

        # Récupère et ajoute le fingerprint du serveur SFTP à la liste des fingerprints autorisés
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(settings.SFTP_HOST, settings.SFTP_PORT, settings.SFTP_USERNAME, settings.SFTP_PASSWORD)
        fingerprint = client.get_transport().get_remote_server_key().fingerprint
        original_fingerprints = CleverCloudSftpVerifier.CLEVER_CLOUD_FINGERPRINTS.copy()
        CleverCloudSftpVerifier.CLEVER_CLOUD_FINGERPRINTS.append(fingerprint)

        # 1. Sauvegarde la valeur initiale du hostname attendu pour pouvoir la restaurer plus tard
        # 2. Modifie temporairement le hostname attendu pour qu'il corresponde au format spécial de Paramiko
        #    Lorsque Paramiko se connecte à un serveur SFTP, il formate le hostname comme "[localhost]:62525"
        #    Cette modification permet à notre vérificateur CleverCloudSftpVerifier d'accepter cette connexion
        #    au conteneur SFTPContainer au lieu de la rejeter comme une connexion non autorisée
        #
        #    Dans notre test, le conteneur SFTP expose le port 22 sur un port aléatoire (comme 62525)
        #    à cause du mapping de port fait par le conteneur SFTPContainer.
        #    Sans cette adaptation, notre vérificateur CleverCloudSftpVerifier rejetterait la connexion car il comparerait
        #    simplement "localhost" avec "[localhost]:62525"
        original_expected_hostname = CleverCloudSftpVerifier.EXPECTED_HOSTNAME
        CleverCloudSftpVerifier.EXPECTED_HOSTNAME = f"[{settings.SFTP_HOST}]:{settings.SFTP_PORT}"

        call_command("fetch_export_agricoll_contacts_file")

        CleverCloudSftpVerifier.CLEVER_CLOUD_FINGERPRINTS = original_fingerprints
        CleverCloudSftpVerifier.EXPECTED_HOSTNAME = original_expected_hostname
