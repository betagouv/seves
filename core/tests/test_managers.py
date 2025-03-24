from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.factories import DocumentFactory, UserFactory, ContactStructureFactory, ContactAgentFactory, StructureFactory
from core.models import Document, Contact
from sv.factories import EvenementFactory

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


@pytest.mark.django_db
def test_order_by_structure_and_name():
    structure_bsv = StructureFactory(niveau1="AC/DAC/DGAL", niveau2="BSV", libelle="BSV")
    structure_ddpp17 = StructureFactory(niveau1="DDI/DDPP", niveau2="DDPP17", libelle="DDPP17")
    structure_mus = StructureFactory(niveau1="AC/DAC/DGAL", niveau2="MUS", libelle="MUS")
    contact_mus = ContactAgentFactory(agent__structure=structure_mus, agent__nom="Petit", agent__prenom="Thomas")
    contact_bsv1 = ContactAgentFactory(agent__structure=structure_bsv, agent__nom="Dubois", agent__prenom="Martin")
    contact_ddpp1 = ContactAgentFactory(agent__structure=structure_ddpp17, agent__nom="Leroy", agent__prenom="Julie")
    contact_bsv2 = ContactAgentFactory(agent__structure=structure_bsv, agent__nom="Martin", agent__prenom="Sophie")
    contact_ddpp2 = ContactAgentFactory(
        agent__structure=structure_ddpp17, agent__nom="Bernard", agent__prenom="Camille"
    )
    evenement = EvenementFactory()
    evenement.contacts.set([contact_mus, contact_bsv1, contact_ddpp1, contact_bsv2, contact_ddpp2])

    ordered_contacts = evenement.contacts.agents_only().order_by_structure_and_name()

    assert list(ordered_contacts) == [
        contact_bsv1,
        contact_bsv2,
        contact_ddpp2,
        contact_ddpp1,
        contact_mus,
    ]
