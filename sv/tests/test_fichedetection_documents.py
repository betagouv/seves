from playwright.sync_api import Page, expect
from ..models import FicheDetection

def test_can_add_document_to_fiche_detection(
    live_server, page: Page, fiche_detection: FicheDetection
):
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_test_id("documents-add")).to_be_visible()
    page.get_by_test_id("documents-add").click()

    expect(page.locator("#fr-modal-2-title")).to_be_visible()

    page.locator("#id_nom").fill("Name of the document")
    page.locator("#id_document_type").select_option("autre")
    page.locator("#id_description").fill("Description")
    page.locator("#id_file").set_input_files('README.md')
    page.get_by_test_id("documents-send").click()

    page.wait_for_timeout(200)
    assert fiche_detection.documents.count() == 1
    document = fiche_detection.documents.get()

    assert document.document_type == "autre"
    assert document.nom == "Name of the document"
    assert document.description == "Description"

    # Check the document is now listed on the page
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Name of the document")).to_be_visible()