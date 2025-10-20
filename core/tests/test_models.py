from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from core.factories import ContactAgentFactory
from core.models import Structure, LienLibre, Contact, Agent


@pytest.mark.django_db
def test_cant_create_freelink_on_same_object():
    structure_1 = Structure.objects.create(niveau1="Foo")
    content_type = ContentType.objects.get_for_model(structure_1)

    with pytest.raises(IntegrityError):
        LienLibre.objects.create(
            content_type_1=content_type,
            object_id_1=structure_1.id,
            content_type_2=content_type,
            object_id_2=structure_1.id,
        )


@pytest.mark.django_db
def test_cant_create_freelink_if_inverted_relation_exists():
    contact_1 = ContactAgentFactory()
    contact_2 = ContactAgentFactory()
    content_type = ContentType.objects.get_for_model(contact_1)
    LienLibre.objects.create(
        content_type_1=content_type, object_id_1=contact_1.id, content_type_2=content_type, object_id_2=contact_2.id
    )

    with pytest.raises(ValidationError):
        LienLibre.objects.create(
            content_type_1=content_type,
            object_id_1=contact_2.id,
            content_type_2=content_type,
            object_id_2=contact_1.id,
        )


@pytest.mark.django_db
def test_can_create_contact_with_structure_only():
    structure = Structure.objects.create(niveau1="Structure A")
    contact = Contact.objects.create(structure=structure)
    assert contact.structure == structure
    assert contact.agent is None


@pytest.mark.django_db
def test_can_create_contact_with_agent_only():
    structure = Structure.objects.create(niveau1="Structure A")
    User = get_user_model()
    user = User.objects.create(username="test")
    agent = Agent.objects.create(user=user, structure=structure)
    contact = Contact.objects.create(agent=agent)
    assert contact.agent == agent
    assert contact.structure is None


@pytest.mark.django_db
def test_cant_create_contact_with_both_structure_and_agent():
    structure = Structure.objects.create(niveau1="Structure A")
    structure_agent = Structure.objects.create(niveau1="Structure de l'agent")
    User = get_user_model()
    user = User.objects.create(username="test")
    agent = Agent.objects.create(user=user, structure=structure_agent)
    with pytest.raises(IntegrityError):
        Contact.objects.create(structure=structure, agent=agent)


@pytest.mark.django_db
def test_cant_create_contact_with_no_structure_and_no_agent():
    with pytest.raises(IntegrityError):
        Contact.objects.create()
