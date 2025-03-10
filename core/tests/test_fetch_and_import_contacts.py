import base64
import csv
import os
import subprocess
import time

import paramiko
from django.contrib.auth import get_user_model
from django.core.management import call_command
from testcontainers.sftp import SFTPContainer

from core.models import Agent, Structure, Contact
from core.tests.test_import_contacts import _reset_contacts


def _create_csv_data_files():
    file_1_data = [
        ["Structure", "Prénom", "Nom", "Mail", "Fonction_hiérarchique", "Complément_fonction", "Téléphone", "Mobile"],
        ["AC/DAC/DGAL/SEVES", "John3", "Doe3", "test3@example3.com", "", "", "", ""],
    ]
    file_2_data = [
        ["Structure", "Prénom", "Nom", "Mail", "Fonction_hiérarchique", "Complément_fonction", "Téléphone", "Mobile"],
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
        ["AC/DAC/DGAL/MUS", "John2", "Doe2", "test2@example2.com", "Super Manager", "", "+33 5 46 01 00 00", ""],
        ["SD/DAAF/DAAF973/SG", "Prestataire", "TEMPORAIRE", "inconnu", "", "", "", ""],
    ]
    for i, data in enumerate([file_1_data, file_2_data], 1):
        with open(f"test{i}.csv", "w", newline="") as f:
            csv.writer(f).writerows(data)


def _generate_private_and_public_keys():
    subprocess.run(["openssl", "genrsa", "-out", "private.key", "4096"])
    with open("private.key", "rb") as f:
        os.environ["SFTP_PRIVATE_KEY"] = base64.b64encode(f.read()).decode("utf-8")
    subprocess.run(["openssl", "rsa", "-in", "private.key", "-pubout", "-out", "public.key"])


def _generate_symmetric_key():
    symmetric_key_result = subprocess.run(["openssl", "rand", "-base64", "128"], capture_output=True, text=True)
    with open("symmetric.key", "w") as f:
        f.write(symmetric_key_result.stdout)


def _generate_encrypted_data_files():
    for i in range(1, 3):
        subprocess.run(
            [
                "openssl",
                "enc",
                "-aes-256-cbc",
                "-a",
                "-salt",
                "-pbkdf2",
                "-in",
                f"test{i}.csv",
                "-out",
                f"test{i}.csv.encrypted",
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


def generate_known_hosts(sftp_container):
    host_ip = sftp_container.get_container_host_ip()
    known_hosts_result = subprocess.run(
        ["ssh-keyscan", "-p", str(sftp_container.get_exposed_sftp_port()), host_ip], capture_output=True, text=True
    )
    return base64.b64encode(known_hosts_result.stdout.encode()).decode("utf-8")


def test_fetch_and_import_contacts_command():
    _reset_contacts()
    _create_csv_data_files()
    _generate_private_and_public_keys()
    _generate_symmetric_key()
    _generate_encrypted_data_files()
    _generate_encrypted_symmetric_key()
    os.remove("test1.csv")
    os.remove("test2.csv")
    os.remove("private.key")
    os.remove("public.key")
    os.remove("symmetric.key")

    with SFTPContainer() as sftp_container:
        sftp_container.start()
        host_ip = sftp_container.get_container_host_ip()
        host_port = sftp_container.get_exposed_sftp_port()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=host_ip,
            port=host_port,
            username=sftp_container.users[0].name,
            password=sftp_container.users[0].password,
        )
        sftp = ssh.open_sftp()
        sftp.chdir("upload")
        sftp.put("symmetric.key.encrypted", "symmetric.key.encrypted")
        sftp.put("test1.csv.encrypted", "test1.csv.encrypted")
        time.sleep(2)  # S'assurer que les timestamps sont différents
        sftp.put("test2.csv.encrypted", "test2.csv.encrypted")
        sftp.close()
        ssh.close()
        os.remove("test1.csv.encrypted")
        os.remove("test2.csv.encrypted")
        os.remove("symmetric.key.encrypted")

        os.environ["SFTP_HOST"] = sftp_container.get_container_host_ip()
        os.environ["SFTP_PORT"] = str(sftp_container.get_exposed_sftp_port())
        os.environ["SFTP_USERNAME"] = sftp_container.users[0].name
        os.environ["SFTP_PASSWORD"] = sftp_container.users[0].password
        os.environ["SFTP_CLEVERCLOUD_KNOWN_HOSTS"] = generate_known_hosts(sftp_container)
        os.environ["SFTP_PATH"] = "upload"

        call_command("fetch_and_import_contacts")

        assert Agent.objects.count() == 2
        assert Structure.objects.count() == 2
        assert Contact.objects.count() == 4
        user_model = get_user_model()
        assert user_model.objects.count() == 2
        assert Contact.objects.filter(first_name="John", last_name="Doe").exists()
        assert Contact.objects.filter(first_name="John2", last_name="Doe2").exists()
        assert not Contact.objects.filter(first_name="John3", last_name="Doe3").exists()
        assert not Contact.objects.filter(first_name="Prestataire", last_name="TEMPORAIRE").exists()
