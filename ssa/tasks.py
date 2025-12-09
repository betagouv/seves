from celery import shared_task

from ssa.export import SsaExport


@shared_task
def export_task(task_id):
    SsaExport().export(task_id)
