from model_bakery import baker
from playwright.sync_api import Page, expect

from core.models import Document
from ..models import FicheDetection


def test_can_add_document_to_fiche_detection(live_server, page: Page, fiche_detection: FicheDetection):
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_test_id("documents-add")).to_be_visible()
    page.get_by_test_id("documents-add").click()

    expect(page.locator("#fr-modal-add-doc")).to_be_visible()

    page.locator("#id_nom").fill("Name of the document")
    page.locator("#id_document_type").select_option("autre")
    page.locator("#id_description").fill("Description")
    page.locator("#id_file").set_input_files("README.md")
    page.get_by_test_id("documents-send").click()

    page.wait_for_timeout(200)
    assert fiche_detection.documents.count() == 1
    document = fiche_detection.documents.get()

    assert document.document_type == "autre"
    assert document.nom == "Name of the document"
    assert document.description == "Description"

    # Check the document is now listed on the page
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Name of the document", exact=True)).to_be_visible()


def test_can_see_and_delete_document_on_fiche_detection(live_server, page: Page, fiche_detection: FicheDetection):
    document = baker.make(Document, nom="Test document", _create_files=True)
    fiche_detection.documents.set([document])
    assert fiche_detection.documents.count() == 1

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_role("heading", name="Test document")).to_be_visible()

    page.locator(f'a[aria-controls="fr-modal-{document.id}"]').click()
    expect(page.locator(f"#fr-modal-{document.id}")).to_be_visible()
    page.get_by_test_id(f"documents-delete-{document.id}").click()

    page.wait_for_timeout(200)
    document = fiche_detection.documents.get()
    assert document.is_deleted is True

    # Document is still displayed
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Test document")).to_be_visible()
    expect(page.get_by_text("Document supprimé")).to_be_visible()


def test_can_edit_document_on_fiche_detection(live_server, page: Page, fiche_detection: FicheDetection):
    document = baker.make(Document, nom="Test document", description="My description", _create_files=True)
    fiche_detection.documents.set([document])
    assert fiche_detection.documents.count() == 1

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_test_id("documents").click()

    expect(page.get_by_role("heading", name="Test document")).to_be_visible()

    page.locator(f'a[aria-controls="fr-modal-edit-{document.id}"]').click()
    expect(page.locator(f"#fr-modal-edit-{document.id}")).to_be_visible()

    page.locator(f"#fr-modal-edit-{document.id} #id_nom").fill("New name")
    page.locator(f"#fr-modal-edit-{document.id} #id_description").fill("")
    page.get_by_test_id(f"documents-edit-{document.pk}").click()

    page.wait_for_url(f"**{fiche_detection.get_absolute_url()}")

    document = fiche_detection.documents.get()
    assert document.nom == "New name"
    assert document.description == ""

    page.get_by_test_id("documents").click()
    expect(page.get_by_text("New name", exact=True)).to_be_visible()
