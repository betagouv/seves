import logging
import os
from urllib.parse import urlparse

from django.conf import settings
import requests

logger = logging.getLogger(__name__)


def scan_document(document) -> bool | None:
    if not (settings.ANTIVIRUS_URL and settings.ANTIVIRUS_TOKEN):
        raise Exception("Cannot scan document, no antivirus is configured")

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

    headers = {
        "accept": "application/json",
        "X-Auth-Token": settings.ANTIVIRUS_TOKEN,
    }
    files = {"file": open(file_path, "rb")}
    try:
        response = requests.post(settings.ANTIVIRUS_URL + "/sync_submit", headers=headers, files=files, timeout=30)
    except Exception as e:
        logger.info(f"Cannot contact antivirus, got {e}")
        return None

    if response.status_code != 200:
        logger.info(f"Could not send document to antivirus got code {response.status_code}")
        return None

    os.remove(file_path)
    return response.json()["is_malware"]
