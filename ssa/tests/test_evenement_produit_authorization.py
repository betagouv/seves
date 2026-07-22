from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
import pytest

from core.factories import AgentFactory
from core.tests.generic_tests.authorization import (
    generic_test_cant_add_agent_without_domain_group,
    generic_test_cant_add_structure_without_domain_group,
    generic_test_cant_cloturer_without_domain_group,
    generic_test_cant_delete_document_without_domain_group,
    generic_test_cant_open_without_domain_group,
    generic_test_cant_publish_without_domain_group,
    generic_test_cant_soft_delete_without_domain_group,
    generic_test_cant_upload_document_without_domain_group,
)
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit


@pytest.mark.django_db
@pytest.mark.disable_mocked_authentification_user
def test_publish_and_ac_notification_view_ignores_domain_group(client):
    agent = AgentFactory()
    user = agent.user
    user.is_active = True
    user.save()
    assert user.groups.count() == 0
    evenement = EvenementProduitFactory(
        createur=agent.structure, etat=EvenementProduit.Etat.BROUILLON, date_publication=None
    )
    client.force_login(user)

    payload = {
        "content_type_id": ContentType.objects.get_for_model(EvenementProduit).id,
        "content_id": evenement.pk,
    }
    response = client.post(reverse("publish-and-ac-notification"), data=payload)

    assert response.status_code == 403

    evenement.refresh_from_db()
    assert evenement.is_published is False
    assert evenement.etat == EvenementProduit.Etat.BROUILLON
    assert evenement.date_publication is None


def test_cant_upload_document_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_cant_upload_document_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_delete_document_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_cant_delete_document_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_add_agent_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_cant_add_agent_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_add_structure_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_cant_add_structure_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_publish_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON, date_publication=None)
    generic_test_cant_publish_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_soft_delete_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_cant_soft_delete_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_cloturer_without_group(client, mocked_authentification_user, mus_contact):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_cant_cloturer_without_domain_group(
        client, mocked_authentification_user, evenement, mus_contact.structure
    )


def test_cant_ouvrir_without_group(client, mocked_authentification_user, mus_contact):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.CLOTURE)
    generic_test_cant_open_without_domain_group(client, mocked_authentification_user, evenement, mus_contact.structure)
