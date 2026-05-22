from celery import shared_task

from ssa.export import SsaExport
from ssa.maestro import send_maestro_webhook
from ssa.models import EvenementProduit


@shared_task
def export_task(task_id):
    SsaExport().export(task_id)


@shared_task()
def notify_maestro(evenement_produit_id):
    evenement_produit = EvenementProduit.objects.get(id=evenement_produit_id)
    send_maestro_webhook(evenement_produit)
