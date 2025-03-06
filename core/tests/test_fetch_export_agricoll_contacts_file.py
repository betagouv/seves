import base64
import csv
import os
import subprocess
import tempfile
import time

import paramiko
import pytest
from _pytest.fixtures import fixture
from django.contrib.auth import get_user_model
from django.core.management import call_command
from testcontainers.sftp import SFTPContainer

from core.agricoll import CleverCloudSftpVerifier, SftpAgricoll
from core.models import Agent, Structure, Contact
from core.tests.test_import_contacts import _reset_contacts


def _create_csv_data_file():
    with open("test.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(
            [
                [
                    "Structure",
                    "Prénom",
                    "Nom",
                    "Mail",
                    "Fonction_hiérarchique",
                    "Complément_fonction",
                    "Téléphone",
                    "Mobile",
                ],
                [
                    "DDI/DDPP/DDPP17/SSA",
                    "John",
                    "Doe",
                    "test@example.com",
                    "Manager",
                    "",
                    "+33 5 46 00 00 00",
                    "+33 6 00 00 00 00",
                ],
                [
                    "AC/DAC/DGAL/MUS",
                    "John2",
                    "Doe2",
                    "test2@example2.com",
                    "Super Manager",
                    "",
                    "+33 5 46 01 00 00",
                    "",
                ],
                ["SD/DAAF/DAAF973/SG", "Prestataire", "TEMPORAIRE", "inconnu", "", "", "", ""],
            ]
        )


def _generate_private_and_public_keys():
    subprocess.run(["openssl", "genrsa", "-out", "private.key", "4096"])
    with open("private.key", "rb") as f:
        os.environ["SFTP_PRIVATE_KEY"] = base64.b64encode(f.read()).decode("utf-8")
    subprocess.run(["openssl", "rsa", "-in", "private.key", "-pubout", "-out", "public.key"])


def _generate_symmetric_key():
    symmetric_key_result = subprocess.run(["openssl", "rand", "-base64", "128"], capture_output=True, text=True)
    with open("symmetric.key", "w") as f:
        f.write(symmetric_key_result.stdout)


def _generate_encrypted_data_file():
    subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-a",
            "-salt",
            "-pbkdf2",
            "-in",
            "test.csv",
            "-out",
            "test.csv.encrypted",
            "-pass",
            "file:symmetric.key",
        ]
    )


def _generate_encrypted_symmetric_key():
    subprocess.run(
        [
            "openssl",
            "pkeyutl",
            "-encrypt",
            "-inkey",
            "public.key",
            "-pubin",
            "-in",
            "symmetric.key",
            "-out",
            "symmetric.key.encrypted",
        ]
    )


@fixture
def setup_sftp_container(settings):
    """
    Fixture qui configure un environnement SFTP pour les tests.
    Retourne un tuple contenant le client SSH et la connexion SFTP.
    Gère automatiquement la restauration de l'environnement après le test.
    """
    original_remote_dir = SftpAgricoll.SFTP_REMOTE_DIRECTORY
    original_fingerprints = CleverCloudSftpVerifier.CLEVER_CLOUD_FINGERPRINTS.copy()
    original_expected_hostname = CleverCloudSftpVerifier.EXPECTED_HOSTNAME

    with SFTPContainer() as sftp_container:
        settings.SFTP_HOST = sftp_container.get_container_host_ip()
        settings.SFTP_PORT = sftp_container.get_exposed_sftp_port()
        settings.SFTP_USERNAME = sftp_container.users[0].name
        settings.SFTP_PASSWORD = sftp_container.users[0].password

        # Surcharge du répertoire d'upload distant car pas les droits d'écrire à la racine sur le SFTP du container
        SftpAgricoll.SFTP_REMOTE_DIRECTORY = "upload"

        # Récupère et ajoute le fingerprint du serveur à la liste des fingerprints autorisés
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(settings.SFTP_HOST, settings.SFTP_PORT, settings.SFTP_USERNAME, settings.SFTP_PASSWORD)
        fingerprint = client.get_transport().get_remote_server_key().fingerprint
        CleverCloudSftpVerifier.CLEVER_CLOUD_FINGERPRINTS.append(fingerprint)

        # Adapte le format du hostname attendu pour Paramiko (format "[localhost]:62525")
        # Permet au CleverCloudSftpVerifier d'accepter les connexions au conteneur SFTPContainer
        # malgré le mapping de port aléatoire du conteneur (ex: port 22 → 62525)
        CleverCloudSftpVerifier.EXPECTED_HOSTNAME = f"[{settings.SFTP_HOST}]:{settings.SFTP_PORT}"

        sftp = client.open_sftp()

        try:
            yield client, sftp
        finally:
            SftpAgricoll.SFTP_REMOTE_DIRECTORY = original_remote_dir
            CleverCloudSftpVerifier.CLEVER_CLOUD_FINGERPRINTS = original_fingerprints
            CleverCloudSftpVerifier.EXPECTED_HOSTNAME = original_expected_hostname


def test_fetch_export_agricoll_contacts_command(settings, setup_sftp_container):
    _reset_contacts()
    _create_csv_data_file()
    _generate_private_and_public_keys()
    _generate_symmetric_key()
    _generate_encrypted_data_file()
    _generate_encrypted_symmetric_key()
    os.remove("test.csv")
    os.remove("private.key")
    os.remove("public.key")
    os.remove("symmetric.key")

    client, sftp = setup_sftp_container
    sftp.put("test.csv.encrypted", "upload/test.csv.encrypted")
    sftp.put("symmetric.key.encrypted", "upload/symmetric.key.encrypted")
    os.remove("test.csv.encrypted")
    os.remove("symmetric.key.encrypted")

    call_command("fetch_and_import_agricoll_contacts")

    assert Agent.objects.count() == 2
    assert Structure.objects.count() == 2
    assert Contact.objects.count() == 4
    user_model = get_user_model()
    assert user_model.objects.count() == 2


@pytest.mark.parametrize(
    "file_suffix, download_method, file_path_attr",
    [
        (".csv.encrypted", "download_latest_encrypted_data_file", "encrypted_data_file_path"),
        (".key.encrypted", "download_latest_encrypted_symmetric_key_file", "encrypted_symmetric_key_file_path"),
    ],
)
def test_download_latest_file(settings, setup_sftp_container, file_suffix, download_method, file_path_attr):
    with tempfile.TemporaryDirectory() as temp_dir:
        old_file_path = os.path.join(temp_dir, f"old_file{file_suffix}")
        new_file_path = os.path.join(temp_dir, f"new_file{file_suffix}")

        with open(old_file_path, "w") as f:
            f.write("Ancien fichier")
        with open(new_file_path, "w") as f:
            f.write("Nouveau fichier")

        client, sftp = setup_sftp_container
        sftp.put(old_file_path, f"upload/old_file{file_suffix}")
        time.sleep(2)  # S'assurer que les timestamps sont différents
        sftp.put(new_file_path, f"upload/new_file{file_suffix}")

        sftp_agricoll = SftpAgricoll()
        sftp_agricoll.connect_to_sftp()
        method = getattr(sftp_agricoll, download_method)
        method()
        result_path = getattr(sftp_agricoll, file_path_attr)
        with open(result_path, "r") as f:
            content = f.read()
        assert content == "Nouveau fichier"

        os.remove(result_path)
        sftp_agricoll.close_connections()
