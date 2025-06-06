from playwright.sync_api import Page

from core.pages import WithDocumentsPage


def generic_test_cant_see_document_type_from_other_app(
    live_server, page: Page, check_select_options_from_element, object
):
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    document_page = WithDocumentsPage(page)
    document_page.open_document_tab()
    document_page.open_add_document()
    expected = [c.label for c in object.get_allowed_document_types()]
    check_select_options_from_element(document_page.add_document_types, expected, with_default_value=False)
