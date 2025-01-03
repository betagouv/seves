from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from model_bakery import baker
from playwright.sync_api import Page, expect

from core.models import Structure, Document, Visibilite
from django.contrib.auth import get_user_model

User = get_user_model()


def test_can_add_document_to_fiche_detection(
    live_server, page: Page, fiche_variable, mocked_authentification_user: User
):
    fiche = fiche_variable()
    page.goto(f"{live_server.url}{fiche.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_test_id("documents-add")).to_be_visible()
    page.get_by_test_id("documents-add").click()

    expect(page.locator("#fr-modal-add-doc")).to_be_visible()

    page.locator("#id_nom").fill("Name of the document")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#id_description").fill("Description")
    page.locator("#id_file").set_input_files("README.md")
    page.get_by_test_id("documents-send").click()

    assert fiche.documents.count() == 1
    document = fiche.documents.get()

    assert document.document_type == Document.TypeDocument.COMPTE_RENDU_REUNION
    assert document.nom == "Name of the document"
    assert document.description == "Description"
    assert document.created_by == mocked_authentification_user.agent
    assert document.created_by_structure == mocked_authentification_user.agent.structure

    # Check the document is now listed on the page
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Name of the document Information")).to_be_visible()
    expect(page.get_by_text(str(mocked_authentification_user.agent.structure).upper(), exact=True)).to_be_visible()
    expect(page.locator(".document__details--type", has_text=f"{document.get_document_type_display()}")).to_be_visible()


def test_can_see_and_delete_document_on_fiche_detection(
    live_server, page: Page, fiche_variable, mocked_authentification_user: User, document_recipe
):
    fiche = fiche_variable()
    document = document_recipe().make(nom="Test document", description="")
    fiche.documents.set([document])
    assert fiche.documents.count() == 1

    page.goto(f"{live_server.url}{fiche.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Test document", exact=True)).to_be_visible()

    page.locator(f'a[aria-controls="fr-modal-{document.id}"]').click()
    expect(page.locator(f"#fr-modal-{document.id}")).to_be_visible()
    page.get_by_test_id(f"documents-delete-{document.id}").click()

    page.wait_for_timeout(600)
    document = fiche.documents.get()
    assert document.is_deleted is True
    assert document.deleted_by == mocked_authentification_user.agent

    # Document is still displayed
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Test document")).to_be_visible()
    expect(page.get_by_text("Document supprimé")).to_be_visible()


def test_can_edit_document_on_fiche_detection(live_server, page: Page, fiche_variable, document_recipe):
    fiche = fiche_variable()
    document = document_recipe().make(nom="Test document", description="My description")
    fiche.documents.set([document])
    assert fiche.documents.count() == 1

    page.goto(f"{live_server.url}{fiche.get_absolute_url()}")
    page.get_by_test_id("documents").click()

    expect(page.get_by_text("Test document Information")).to_be_visible()

    page.locator(f'a[aria-controls="fr-modal-edit-{document.id}"]').click()
    expect(page.locator(f"#fr-modal-edit-{document.id}")).to_be_visible()

    page.locator(f"#fr-modal-edit-{document.id} #id_nom").fill("New name")
    page.locator(f"#fr-modal-edit-{document.id} #id_description").fill("")
    page.get_by_test_id(f"documents-edit-{document.pk}").click()

    page.wait_for_url(f"**{fiche.get_absolute_url()}#tabpanel-documents-panel")

    document = fiche.documents.get()
    assert document.nom == "New name"
    assert document.description == ""

    page.get_by_test_id("documents").click()
    expect(page.get_by_text("New name", exact=True)).to_be_visible()


def test_can_filter_documents_by_type_on_fiche_detection(live_server, page: Page, fiche_variable, document_recipe):
    fiche = fiche_variable()
    document_1 = document_recipe().make(nom="Test document", document_type="autre", description="")
    document_2 = document_recipe().make(nom="Ma carto", document_type="cartographie", description="")
    fiche.documents.set([document_1, document_2])

    page.goto(f"{live_server.url}{fiche.get_absolute_url()}#tabpanel-documents-panel")

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).to_be_visible()

    page.locator(".documents__filters #id_document_type").select_option("autre")
    page.get_by_test_id("documents-filter").click()

    assert (
        page.url
        == f"{live_server.url}{fiche.get_absolute_url()}?document_type=autre&created_by_structure=#tabpanel-documents-panel"
    )

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).not_to_be_visible()


def test_can_filter_documents_by_unit_on_fiche_detection(live_server, page: Page, fiche_variable, document_recipe):
    fiche = fiche_variable()
    document_1 = document_recipe().make(nom="Test document", document_type="autre", description="")
    other_structure = baker.make(Structure)
    document_2 = document_recipe().make(
        nom="Ma carto", document_type="cartographie", description="", created_by_structure=other_structure
    )
    _structure_with_no_document = baker.make(Structure, libelle="Should not be in the list")
    fiche.documents.set([document_1, document_2])

    page.goto(f"{live_server.url}{fiche.get_absolute_url()}#tabpanel-documents-panel")

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).to_be_visible()

    assert page.locator(".documents__filters #id_created_by_structure").all_inner_texts() == [
        "\n".join(["---------", "Structure Test"])
    ]
    page.locator(".documents__filters #id_created_by_structure").select_option("Structure Test")
    page.get_by_test_id("documents-filter").click()

    assert (
        page.url
        == f"{live_server.url}{fiche.get_absolute_url()}?document_type=&created_by_structure={document_1.created_by_structure.id}#tabpanel-documents-panel"
    )

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).not_to_be_visible()


def test_cant_add_document_if_brouillon(client, fiche_variable):
    fiche = fiche_variable()
    fiche.visibilite = Visibilite.BROUILLON
    fiche.numero = None
    fiche.save()
    test_file = SimpleUploadedFile(name="test.pdf", content=b"contenu du fichier test", content_type="application/pdf")
    data = {
        "nom": "Un fichier test",
        "document_type": Document.TypeDocument.AUTRE,
        "description": "Description du fichier test",
        "file": test_file,
        "content_type": ContentType.objects.get_for_model(fiche).pk,
        "object_id": fiche.id,
        "next": fiche.get_absolute_url(),
    }

    response = client.post(
        reverse("document-upload"),
        data=data,
        format="multipart",
        follow=True,
    )

    assert response.status_code == 200
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_cant_delete_document_if_brouillon(client, fiche_variable, document_recipe):
    fiche = fiche_variable()
    fiche.visibilite = Visibilite.BROUILLON
    fiche.numero = None
    fiche.save()
    document = document_recipe().make(nom="Test document", description="un document")
    fiche.documents.set([document])

    response = client.post(
        reverse("document-delete", kwargs={"pk": document.pk}),
        data={"next": fiche.get_absolute_url()},
        follow=True,
    )
    document.refresh_from_db()

    assert document.is_deleted is False
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_cant_edit_document_if_brouillon(client, fiche_variable, document_recipe):
    fiche = fiche_variable()
    fiche.visibilite = Visibilite.BROUILLON
    fiche.numero = None
    fiche.save()
    document = document_recipe().make(nom="Test document", description="un document")
    fiche.documents.set([document])

    response = client.post(
        reverse("document-update", kwargs={"pk": document.pk}),
        data={"next": fiche.get_absolute_url(), "nom": "Nouveau nom", "description": "Nouvelle description"},
        follow=True,
    )
    document.refresh_from_db()

    assert document.nom == "Test document"
    assert document.description == "un document"
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"
