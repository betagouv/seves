from playwright.sync_api import Page

from core.tests.generic_tests.documents import (
    generic_test_cant_see_document_type_from_other_app,
    generic_test_can_add_document_to_evenement,
    generic_test_document_modal_front_behavior,
)
from tiac.factories import EvenementSimpleFactory
from tiac.models import EvenementSimple


def test_can_add_document_to_evenement(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_document_to_evenement(live_server, page, mocked_authentification_user, evenement)


def test_cant_see_document_type_from_other_app(live_server, page: Page, check_select_options_from_element):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_cant_see_document_type_from_other_app(live_server, page, check_select_options_from_element, evenement)


def test_document_modal_front_behavior(live_server, page: Page):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_document_modal_front_behavior(live_server, page, evenement)
