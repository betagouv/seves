from playwright.sync_api import Page

from core.tests.generic_tests.documents import (
    generic_test_cant_see_document_type_from_other_app,
    generic_test_can_add_document_to_evenement,
)
from tiac.factories import InvestigationTiacFactory
from tiac.models import InvestigationTiac


def test_can_add_document_to_evenement(live_server, page: Page, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_add_document_to_evenement(live_server, page, mocked_authentification_user, evenement)


def test_cant_see_document_type_from_other_app(live_server, page: Page, check_select_options_from_element):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_cant_see_document_type_from_other_app(live_server, page, check_select_options_from_element, evenement)
