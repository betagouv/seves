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
from tiac.factories import EvenementSimpleFactory
from tiac.models import EvenementSimple


def test_cant_upload_document_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_cant_upload_document_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_delete_document_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_cant_delete_document_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_add_agent_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_cant_add_agent_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_add_structure_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_cant_add_structure_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_publish_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.BROUILLON, date_publication=None)
    generic_test_cant_publish_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_soft_delete_without_domain_group(client, mocked_authentification_user):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_cant_soft_delete_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_cloturer_without_group(client, mocked_authentification_user, mus_contact):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_cant_cloturer_without_domain_group(
        client, mocked_authentification_user, evenement, mus_contact.structure
    )


def test_cant_ouvrir_without_group(client, mocked_authentification_user, mus_contact):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.CLOTURE)
    generic_test_cant_open_without_domain_group(client, mocked_authentification_user, evenement, mus_contact.structure)
