from django.core.management import call_command
from django.core.management.base import BaseCommand

from core.agricoll import SftpAgricoll


class Command(BaseCommand):
    help = "Récupère et déchiffre les fichiers (export contacts agricoll et clé symétrique) les plus récents depuis le SFTP client puis importe les contacts"

    def handle(self, *args, **options):
        try:
            sftp_agricoll = SftpAgricoll()
            sftp_agricoll.connect_to_sftp()
            sftp_agricoll.download_latest_encrypted_data_file()
            sftp_agricoll.download_latest_encrypted_symmetric_key_file()
            sftp_agricoll.decrypt_symmetric_key()
            contacts_agricoll_file_path = sftp_agricoll.decrypt_data_file()
            call_command("import_contacts", contacts_agricoll_file_path)
            sftp_agricoll.clean_files()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur : {str(e)}"))
        finally:
            sftp_agricoll.close_connections()
