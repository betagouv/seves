import logging

from django.conf import settings
import requests
from requests import ConnectTimeout

from ssa.models import EvenementProduit

logger = logging.getLogger(__name__)


def send_maestro_webhook(evenement_produit: EvenementProduit):
    if not settings.MAESTRO_WEBHOOK_URL:
        return
    payload = {
        "maestro_reference": evenement_produit.maestro_reference,
        "seves_id": evenement_produit.id,
        "seves_numero": evenement_produit.numero,
    }
    headers = {"Authorization": settings.MAESTRO_TOKEN, "Content-Type": "application/json"}
    try:
        response = requests.put(settings.MAESTRO_WEBHOOK_URL, json=payload, headers=headers, timeout=15)
    except ConnectTimeout as e:
        logger.info(f"Cannot contact MAESTRO, timeout with {e}")
        return None
    if response.status_code != 200:
        logger.error(f"Unknown status code from MAESTRO, got {response.status_code}: {response}")
