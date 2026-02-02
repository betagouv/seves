from threading import Lock
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.forms import Form
from playwright.sync_api import Page, expect

from core.factories import DocumentFactory
from core.models import Document
from core.pages import WithDocumentsPage
from seves import settings


def generic_test_cant_see_document_type_from_other_app(
    live_server, page: Page, check_select_options_from_element, object
):
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    document_page = WithDocumentsPage(page)
    document_page.open_document_tab()
    document_page.open_document_modal()
    expected = [settings.SELECT_EMPTY_CHOICE, *[t.label for t in object.get_allowed_document_types()]]
    check_select_options_from_element(document_page.global_document_type_input, expected, with_default_value=False)


def generic_test_can_add_document_to_evenement(live_server, page: Page, mocked_authentification_user, object):
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    previous = object.documents.count()

    document_page = WithDocumentsPage(page)
    document_page.add_basic_document()
    document_page.validate_document_modal()

    object.refresh_from_db()
    assert object.documents.count() == previous + 1
    document = object.documents.get()

    assert document.document_type == Document.TypeDocument.AUTRE
    assert document.nom == document_page.BASIC_DOCUMENT_NAME
    assert document.description == "Ma description"
    assert document.created_by == mocked_authentification_user.agent
    assert document.created_by_structure == mocked_authentification_user.agent.structure

    # Check the document is now listed on the page
    document_page.open_document_tab()
    expect(page.get_by_text(f"{document_page.BASIC_DOCUMENT_NAME} Information")).to_be_visible()
    expect(page.get_by_text(str(mocked_authentification_user.agent.structure).upper(), exact=True)).to_be_visible()
    expect(page.locator(".fr-tag", has_text=f"{document.get_document_type_display()}")).to_be_visible()


def generic_test_can_retry_on_data_error(live_server, page: Page, object):
    object.documents.set(DocumentFactory.create_batch(4, content_object=object))
    previous = object.documents.count()
    ok_marker = "ok"

    class SideEffect:
        """
        This class will simulate a form error the first time a document without 'ok' in its name is submitted
        It is thread-safe to prevent messing with parallel queries.
        """

        def __init__(self):
            self.first_call = True
            self.lock = Lock()  # Prevents problems with Django's request threads

        def __call__(self, form: Form, *args, **kwargs):
            with self.lock:
                if ok_marker not in form.cleaned_data.get("nom") and self.first_call:
                    self.first_call = False
                    form.add_error("file", ValidationError("Fail first"))
                return form.cleaned_data.get("file")

    side_effect = SideEffect()

    with patch("core.views.DocumentUploadForm.clean_file", autospec=True, wraps=True) as clean_file_mock:
        clean_file_mock.side_effect = side_effect

        page.goto(f"{live_server.url}{object.get_absolute_url()}")

        document_page = WithDocumentsPage(page)
        document_page.add_basic_document(close=False)
        document_page.add_basic_document(suffix=ok_marker, close=False)

        # First submission; request should fail on error
        document_page.modal_submit_btn.click()
        expect(document_page.document_modal).to_contain_text("Il y a une erreur dans ce formulaire")

        # Second submission ok
        document_page.validate_document_modal()

        object.refresh_from_db()
        assert object.documents.count() == previous + 2
