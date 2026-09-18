from celery import shared_task

from sa.export import SaExport


@shared_task
def export_sa_task(task_id):
    SaExport().export(task_id)
