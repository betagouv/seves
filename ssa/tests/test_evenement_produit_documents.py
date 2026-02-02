from playwright.sync_api import Page
from playwright.sync_api import expect

from core.factories import DocumentFactory
from core.pages import WithDocumentsPage
from core.tests.generic_tests.documents import (
    generic_test_cant_see_document_type_from_other_app,
    generic_test_can_add_document_to_evenement,
    generic_test_can_retry_on_data_error,
)
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit


def test_can_add_document_to_evenement(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_add_document_to_evenement(live_server, page, mocked_authentification_user, evenement)


def test_can_retry_on_data_error(live_server, page: Page):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_retry_on_data_error(live_server, page, evenement)


def test_can_edit_document_on_evenement(live_server, page: Page):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    document = DocumentFactory(content_object=evenement, nom="Test document", description="My description")
    evenement.documents.set([document])
    assert evenement.documents.count() == 1

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    document_page = WithDocumentsPage(page)
    document_page.open_document_tab()
    assert "Test document" in document_page.document_title(document.pk).text_content()

    document_page.open_edit_document(document.id)
    document_page.document_edit_title(document.id).fill("New name")
    document_page.document_edit_description(document.id).fill("")
    document_page.document_edit_save(document.id)

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-documents-panel")

    document = evenement.documents.get()
    assert document.nom == "New name"
    assert document.description == ""

    document_page.open_document_tab()
    expect(document_page.document_title(document.pk)).to_be_visible()
    expect(document_page.document_title(document.pk)).to_have_text("New name")


def test_cant_see_document_type_from_other_app(live_server, page: Page, check_select_options_from_element):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_cant_see_document_type_from_other_app(live_server, page, check_select_options_from_element, evenement)
