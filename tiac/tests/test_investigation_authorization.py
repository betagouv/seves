from core.tests.generic_tests.authorization import (
    generic_test_cant_add_agent_without_domain_group,
    generic_test_cant_add_structure_without_domain_group,
    generic_test_cant_delete_document_without_domain_group,
    generic_test_cant_publish_without_domain_group,
    generic_test_cant_soft_delete_without_domain_group,
    generic_test_cant_upload_document_without_domain_group,
)
from tiac.factories import InvestigationTiacFactory
from tiac.models import InvestigationTiac


def test_cant_upload_document_without_domain_group(client, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_cant_upload_document_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_delete_document_without_domain_group(client, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_cant_delete_document_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_add_agent_without_domain_group(client, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_cant_add_agent_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_add_structure_without_domain_group(client, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_cant_add_structure_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_publish_without_domain_group(client, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.BROUILLON, date_publication=None)
    generic_test_cant_publish_without_domain_group(client, mocked_authentification_user, evenement)


def test_cant_soft_delete_without_domain_group(client, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_cant_soft_delete_without_domain_group(client, mocked_authentification_user, evenement)
