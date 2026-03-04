from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from core.models import Document
from core.notifications import notify_document_upload
from ssa.models import EvenementInvestigationCasHumain, EvenementProduit


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        content_type_1 = ContentType.objects.get_for_model(EvenementProduit)
        content_type_2 = ContentType.objects.get_for_model(EvenementInvestigationCasHumain)

        base_queryset = Document.objects.filter(notification_sent=False, document_type__in=Document.NEED_NOTIFICATION)
        base_queryset = base_queryset.filter(content_type_id__in=[content_type_1.id, content_type_2.id])
        groups = base_queryset.values("content_type", "object_id").annotate(count=Count("id"))
        for group in groups:
            with transaction.atomic():
                docs = base_queryset.select_for_update().filter(
                    content_type_id=group["content_type"],
                    object_id=group["object_id"],
                )
                if not docs.exists():
                    continue

                notify_document_upload(docs[0].content_object, docs)
                docs.update(notification_sent=True)
