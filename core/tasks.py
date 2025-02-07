from celery import shared_task
import os
import subprocess
import requests

from core.models import Document
from django.conf import settings
from urllib.parse import urlparse


@shared_task
def scan_for_viruses(document_pk):
    document = Document.objects.get(pk=document_pk)
    parsed_url = urlparse(document.file.url)
    file_path = os.path.join(str(document.pk))

    if parsed_url.scheme in ["http", "https"]:
        response = requests.get(document.file.url, stream=True)
        file_path = os.path.join(str(document.pk))
        with open(file_path, "wb+") as f:
            for chunk in response.iter_content(chunk_size=8192):
                _ = f.write(chunk)
    else:
        with open(document.file.path, "rb") as src, open(file_path, "wb+") as destination:
            destination.write(src.read())

    config_option = f"--config={settings.CLAMAV_CONFIG_FILE}"
    result = subprocess.run(
        ["clamdscan", config_option, "--fdpass", file_path],
        capture_output=True,
        text=True,
    )
    match result.returncode:
        case 0:
            document.is_infected = False
            document.save()
        case 1:
            document.is_infected = True
            document.save()
        case _:
            raise Exception(result.stdout)

    os.remove(file_path)
