from core.models import Document, Structure, Agent
import pytest
from datetime import datetime
from model_bakery import baker
from django.utils import timezone


@pytest.mark.django_db
def test_document_ordered():
    agent = baker.make(Agent)
    structure = baker.make(Structure)
    doc_1 = baker.make(
        Document,
        nom="Doc 1",
        date_creation=timezone.make_aware(datetime(2024, 5, 5)),
        created_by=agent,
        created_by_structure=structure,
        is_deleted=True,
    )
    doc_2 = baker.make(
        Document,
        nom="Doc 2",
        date_creation=timezone.make_aware(datetime(2022, 1, 1)),
        created_by=agent,
        created_by_structure=structure,
    )
    doc_3 = baker.make(
        Document,
        nom="Doc 3",
        date_creation=timezone.make_aware(datetime(2023, 1, 1)),
        created_by=agent,
        created_by_structure=structure,
    )
    doc_4 = baker.make(
        Document,
        nom="Doc 4",
        date_creation=timezone.make_aware(datetime(2024, 1, 1)),
        created_by=agent,
        created_by_structure=structure,
    )

    assert list(Document.objects.order_list()) == [doc_4, doc_3, doc_2, doc_1]
