from django.contrib.auth import get_user_model

from core.models import Document, Structure, Agent, Contact
import pytest
from datetime import datetime
from model_bakery import baker
from django.utils import timezone

User = get_user_model()


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


@pytest.mark.django_db
def test_can_be_emailed():
    Contact.objects.all().delete()
    structure = baker.make(Structure, libelle="Struct")
    contact_for_structure = baker.make(Contact, structure=structure, agent=None, email="foo@bar.com")

    inactive_user = baker.make(User)
    inactive_agent = baker.make(Agent, user=inactive_user)
    _contact_for_inactive_agent = baker.make(Contact, structure=None, agent=inactive_agent)

    active_user = baker.make(User)
    active_user.is_active = True
    active_user.save()
    active_agent = baker.make(Agent, user=active_user)
    contact_for_active_agent = baker.make(Contact, structure=None, agent=active_agent)

    assert list(Contact.objects.can_be_emailed()) == [contact_for_structure, contact_for_active_agent]
