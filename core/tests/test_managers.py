from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.factories import DocumentFactory, UserFactory, ContactStructureFactory, ContactAgentFactory
from core.models import Document, Contact

User = get_user_model()


@pytest.mark.django_db
def test_document_ordered():
    user = UserFactory()
    doc_1 = DocumentFactory(
        is_deleted=True, date_creation=timezone.make_aware(datetime(2024, 5, 5)), content_object=user
    )
    doc_2 = DocumentFactory(date_creation=timezone.make_aware(datetime(2022, 1, 1)), content_object=user)
    doc_3 = DocumentFactory(date_creation=timezone.make_aware(datetime(2023, 1, 1)), content_object=user)
    doc_4 = DocumentFactory(date_creation=timezone.make_aware(datetime(2024, 1, 1)), content_object=user)
    assert list(Document.objects.order_list()) == [doc_4, doc_3, doc_2, doc_1]


@pytest.mark.django_db
def test_can_be_emailed():
    Contact.objects.all().delete()
    contact_for_structure = ContactStructureFactory()

    contact_for_inactive_agent = ContactAgentFactory()
    user = contact_for_inactive_agent.agent.user
    user.is_active = False
    user.save()

    contact_for_active_agent = ContactAgentFactory()
    user = contact_for_active_agent.agent.user
    user.is_active = True
    user.save()

    assert list(Contact.objects.can_be_emailed()) == [contact_for_structure, contact_for_active_agent]
