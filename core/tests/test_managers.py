from core.models import Document
import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_document_ordered():
    doc_1 = baker.make(Document, nom="Doc 1", date_creation="2024-05-05", is_deleted=True)
    doc_2 = baker.make(Document, nom="Doc 2", date_creation="2022-01-01")
    doc_3 = baker.make(Document, nom="Doc 3", date_creation="2023-01-01")
    doc_4 = baker.make(Document, nom="Doc 4", date_creation="2024-01-01")

    assert list(Document.objects.ordered()) == [doc_4, doc_3, doc_2, doc_1]
