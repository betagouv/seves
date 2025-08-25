from playwright.sync_api import Page, expect

from core.models import Document
from core.pages import WithDocumentsPage
from seves import settings


def generic_test_cant_see_document_type_from_other_app(
    live_server, page: Page, check_select_options_from_element, object
):
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    document_page = WithDocumentsPage(page)
    document_page.open_document_tab()
    document_page.open_add_document()
    expected = [settings.SELECT_EMPTY_CHOICE, *[t.label for t in object.get_allowed_document_types()]]
    check_select_options_from_element(document_page.add_document_types, expected, with_default_value=False)


def generic_test_can_add_document_to_evenement(live_server, page: Page, mocked_authentification_user, object):
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    document_page = WithDocumentsPage(page)
    document_page.add_document()

    assert object.documents.count() == 1
    document = object.documents.get()

    assert document.document_type == Document.TypeDocument.AUTRE
    assert document.nom == "Name of the document"
    assert document.description == "Description"
    assert document.created_by == mocked_authentification_user.agent
    assert document.created_by_structure == mocked_authentification_user.agent.structure

    # Check the document is now listed on the page
    document_page.open_document_tab()
    expect(page.get_by_text("Name of the document Information")).to_be_visible()
    expect(page.get_by_text(str(mocked_authentification_user.agent.structure).upper(), exact=True)).to_be_visible()
    expect(page.locator(".fr-tag", has_text=f"{document.get_document_type_display()}")).to_be_visible()
