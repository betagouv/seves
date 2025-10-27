from celery import shared_task

from tiac.export import TiacExport


@shared_task
def export_tiac_task(task_id):
    TiacExport().export(task_id)
