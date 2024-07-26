from model_bakery import baker
from playwright.sync_api import Page, expect
import pytest

from core.models import Structure
from ..models import FicheDetection
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_can_add_document_to_fiche_detection(
    live_server, page: Page, fiche_detection: FicheDetection, mocked_authentification_user: User
):
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_test_id("documents-add")).to_be_visible()
    page.get_by_test_id("documents-add").click()

    expect(page.locator("#fr-modal-add-doc")).to_be_visible()

    page.locator("#id_nom").fill("Name of the document")
    page.locator("#fr-modal-add-doc #id_document_type").select_option("autre")
    page.locator("#id_description").fill("Description")
    page.locator("#id_file").set_input_files("README.md")
    page.get_by_test_id("documents-send").click()

    assert fiche_detection.documents.count() == 1
    document = fiche_detection.documents.get()

    assert document.document_type == "autre"
    assert document.nom == "Name of the document"
    assert document.description == "Description"
    assert document.created_by == mocked_authentification_user.agent
    assert document.created_by_structure == mocked_authentification_user.agent.structure

    # Check the document is now listed on the page
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Name of the document Information")).to_be_visible()
    expect(page.get_by_text(str(mocked_authentification_user.agent.structure).upper(), exact=True)).to_be_visible()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_can_see_and_delete_document_on_fiche_detection(
    live_server, page: Page, fiche_detection: FicheDetection, mocked_authentification_user: User, document_recipe
):
    document = document_recipe().make(nom="Test document", description="")
    fiche_detection.documents.set([document])
    assert fiche_detection.documents.count() == 1

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Test document", exact=True)).to_be_visible()

    page.locator(f'a[aria-controls="fr-modal-{document.id}"]').click()
    expect(page.locator(f"#fr-modal-{document.id}")).to_be_visible()
    page.get_by_test_id(f"documents-delete-{document.id}").click()

    page.wait_for_timeout(200)
    document = fiche_detection.documents.get()
    assert document.is_deleted is True
    assert document.deleted_by == mocked_authentification_user.agent

    # Document is still displayed
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Test document")).to_be_visible()
    expect(page.get_by_text("Document supprimé")).to_be_visible()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_can_edit_document_on_fiche_detection(
    live_server, page: Page, fiche_detection: FicheDetection, document_recipe
):
    document = document_recipe().make(nom="Test document", description="My description")
    fiche_detection.documents.set([document])
    assert fiche_detection.documents.count() == 1

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_test_id("documents").click()

    expect(page.get_by_text("Test document Information")).to_be_visible()

    page.locator(f'a[aria-controls="fr-modal-edit-{document.id}"]').click()
    expect(page.locator(f"#fr-modal-edit-{document.id}")).to_be_visible()

    page.locator(f"#fr-modal-edit-{document.id} #id_nom").fill("New name")
    page.locator(f"#fr-modal-edit-{document.id} #id_description").fill("")
    page.get_by_test_id(f"documents-edit-{document.pk}").click()

    page.wait_for_url(f"**{fiche_detection.get_absolute_url()}#tabpanel-documents-panel")

    document = fiche_detection.documents.get()
    assert document.nom == "New name"
    assert document.description == ""

    page.get_by_test_id("documents").click()
    expect(page.get_by_text("New name", exact=True)).to_be_visible()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_can_filter_documents_by_type_on_fiche_detection(
    live_server, page: Page, fiche_detection: FicheDetection, document_recipe
):
    document_1 = document_recipe().make(nom="Test document", document_type="autre", description="")
    document_2 = document_recipe().make(nom="Ma carto", document_type="cartographie", description="")
    fiche_detection.documents.set([document_1, document_2])

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}#tabpanel-documents-panel")

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).to_be_visible()

    page.locator(".documents__filters #id_document_type").select_option("autre")
    page.get_by_test_id("documents-filter").click()

    assert (
        page.url
        == f"{live_server.url}{fiche_detection.get_absolute_url()}?document_type=autre&created_by_structure=#tabpanel-documents-panel"
    )

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).not_to_be_visible()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_can_filter_documents_by_unit_on_fiche_detection(
    live_server, page: Page, fiche_detection: FicheDetection, document_recipe
):
    document_1 = document_recipe().make(nom="Test document", document_type="autre", description="")
    other_structure = baker.make(Structure)
    document_2 = document_recipe().make(
        nom="Ma carto", document_type="cartographie", description="", created_by_structure=other_structure
    )
    _structure_with_no_document = baker.make(Structure, libelle="Should not be in the list")
    fiche_detection.documents.set([document_1, document_2])

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}#tabpanel-documents-panel")

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).to_be_visible()

    assert page.locator(".documents__filters #id_created_by_structure").all_inner_texts() == [
        "\n".join(["---------", "Structure Test"])
    ]
    page.locator(".documents__filters #id_created_by_structure").select_option("Structure Test")
    page.get_by_test_id("documents-filter").click()

    assert (
        page.url
        == f"{live_server.url}{fiche_detection.get_absolute_url()}?document_type=&created_by_structure={document_1.created_by_structure.id}#tabpanel-documents-panel"
    )

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).not_to_be_visible()
