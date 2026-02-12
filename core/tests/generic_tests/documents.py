from threading import Lock
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.forms import FileField, Form
from django.urls import reverse
from playwright.sync_api import Page, Route, expect
import pytest

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


def generic_test_document_modal_xss_mitigated(live_server, page: Page, content_object):
    DocumentFactory.create_batch(4, content_object=content_object)

    page.goto(f"{live_server.url}{content_object.get_absolute_url()}")
    document_page = WithDocumentsPage(page)

    document_page.open_document_modal()
    # language=html
    document_page.add_basic_document(suffix="><img src=1 onerror=alert(1)>.jpg")
    message_box = page.locator("#tabpanel-documents-panel #document-upload-messages")
    try:
        expect(message_box).to_contain_text(
            "Les fichiers suivants ont été ajoutés avec succès et seront disponibles après l'analyse antivirus :\n"
            "Mon document&gt;&lt;img src=1 onerror=alert(1)&gt;.jpg",
            use_inner_text=True,
        )
    except AssertionError:
        pytest.fail("XSS vulerability on document name")


@patch("core.views.DocumentUploadForm.clean_file", autospec=True, wraps=True)
def generic_test_document_modal_front_behavior(live_server, page: Page, content_object, clean_file_mock):
    """
    This test scenario tests form behavior in 3 cases:
    - one file upload fails with backend failing to validate form
    - one file fails with a network error
    - one file uploads successfully
    It then checks error messages and submits the files agains, this time successfully.
    """
    DocumentFactory.create_batch(4, content_object=content_object)
    previous = content_object.documents.count()
    invalid_marker = "invalid"
    timeout_marker = "timeout"

    class SideEffect:
        """
        This class will simulate a form error the first time a document with 'invalid' in its name is submitted.
        It is thread-safe to prevent messing with parallel queries.
        """

        def __init__(self):
            self.first_call = True
            self.lock = Lock()  # Prevents problems with Django's request threads

        def __call__(self, form: Form, *args, **kwargs):
            with self.lock:
                if invalid_marker in form.cleaned_data.get("nom") and self.first_call:
                    self.first_call = False
                    form.add_error("file", ValidationError(FileField.default_error_messages["empty"]))
                return form.cleaned_data.get("file")

    class RouteHandler:
        """This handler simulates a timeout for one of the file, only the first time"""

        def __init__(self):
            self.first_call = True

        def __call__(self, route: Route):
            content = route.request.post_data_buffer.decode(errors="ignore")
            if f"{WithDocumentsPage.BASIC_DOCUMENT_NAME}{timeout_marker}" in content and self.first_call:
                self.first_call = False
                route.abort("timedout")
            else:
                route.continue_()

    clean_file_mock.side_effect = SideEffect()
    page.route(f"**{reverse('document-upload')}", RouteHandler())

    page.goto(f"{live_server.url}{content_object.get_absolute_url()}")
    document_page = WithDocumentsPage(page)

    # Test step 1
    # Upload is disabled as long as not global document type is set

    document_page.open_document_modal()
    document_page.set_global_document_type("")
    document_page.set_input_file(settings.BASE_DIR / "static/images/login.jpeg")
    assert len(document_page.get_existing_documents_title) == 0
    document_page.close_document_modal_no_validate()

    # Test step 2
    # Try to submit 3 documents, one successfully, one failing with a form validation error,
    # one failing with a network error

    document_page.add_basic_document(close=False)
    document_page.add_basic_document(suffix=invalid_marker, close=False)
    document_page.add_basic_document(suffix=timeout_marker, close=False)
    document_page.validate_document_modal(expect_error=True)

    with document_page.modify_document_by_name(
        f"{document_page.BASIC_DOCUMENT_NAME}{timeout_marker}", validate_modal=False
    ) as accordion:
        expect(accordion).to_contain_text(
            "Il y a eu un problème réseau lors de la soumission du document ; veuillez réessayer."
        )

    with document_page.modify_document_by_name(
        f"{document_page.BASIC_DOCUMENT_NAME}{invalid_marker}", validate_modal=False
    ) as accordion:
        expect(accordion).to_contain_text("Le fichier soumis est vide.")

    # Test step 3
    # Close the modal, ignoring errors on two of the documents, one should exist in DB

    document_page.close_document_modal_no_validate()
    content_object.refresh_from_db()
    assert content_object.documents.count() == previous + 1

    # Test step 4
    # Reopen the modal and submit 2 more documents, one should fail, one should upload successfully, then retry the
    # failing one. Then there should be 3 more documents in DB compared to the beginning of the test.

    clean_file_mock.side_effect.first_call = True
    document_page.add_basic_document(suffix=invalid_marker, close=False)
    document_page.add_basic_document(close=False)
    document_page.validate_document_modal(expect_error=True)
    document_page.validate_document_modal()

    # Test step 5
    # Assert the succes message is disaplayed after redirect and can be closed

    content_object.refresh_from_db()
    last_uploaded = list(content_object.documents.order_by("-date_creation"))[:2]
    message_box = page.locator("#tabpanel-documents-panel #document-upload-messages")
    expect(message_box).to_contain_text(
        "Les fichiers suivants ont été ajoutés avec succès et seront disponibles après l'analyse antivirus :\n"
        f"{'\n'.join([it.nom for it in last_uploaded])}",
        use_inner_text=True,
    )

    message_box.get_by_role("button", name="Masquer le message").click()
    expect(message_box).not_to_be_visible()

    content_object.refresh_from_db()
    assert content_object.documents.count() == previous + 3
