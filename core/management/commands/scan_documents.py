import os
import shutil
import subprocess
from pathlib import Path
import requests
from django.core.management.base import CommandError, BaseCommand

from core.models import Document
from django.conf import settings


class Command(BaseCommand):
    help = "Run ClamAV antivirus scan on files hosted in an S3 like bucket."
    BATCH_SIZE = 200

    def results(self, stdout_txt):
        viruses_pk = []
        for line in stdout_txt.splitlines():
            local_path, _details = line.split(":", maxsplit=1)
            viruses_pk.append(local_path.split("/")[-1])
        return viruses_pk

    def download_documents(self, documents, workdir):
        for document in documents:
            response = requests.get(document.file.url, stream=True)
            file_path = os.path.join(workdir, str(document.pk))
            with open(file_path, "wb+") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    _ = f.write(chunk)

    def handle(self, *args, **options):
        documents_to_analyze = Document._base_manager.exclude(file="").filter(is_infected__isnull=True)
        documents_to_analyze[: self.BATCH_SIZE].select_for_update()
        try:
            os.mkdir("for_analysis")
        except FileExistsError:
            pass

        workdir = Path("for_analysis")
        self.download_documents(documents_to_analyze, workdir)
        config_option = f"--config={settings.CLAMAV_CONFIG_FILE}"
        result = subprocess.run(
            ["clamdscan", "--no-summary", "--infected", config_option, "--fdpass", workdir],
            capture_output=True,
            text=True,
        )
        match result.returncode:
            case 0:
                viruses_pk = []
            case 1:
                viruses_pk = self.results(result.stdout)
            case _:
                raise CommandError(result.stderr)

        for document in documents_to_analyze:
            document = Document._base_manager.get(pk=document.pk)
            document.is_infected = str(document.pk) in viruses_pk
            document.save()

        shutil.rmtree(workdir)
        self.stdout.write(f"Analyzed {documents_to_analyze.count()} documents")
