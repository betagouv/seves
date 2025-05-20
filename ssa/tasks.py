from celery import shared_task

from ssa.export import EvenementProduitExport


@shared_task
def export_task(task_id):
    EvenementProduitExport().export(task_id)
