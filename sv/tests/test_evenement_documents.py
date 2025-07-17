import os
import tempfile
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from playwright.sync_api import Page, expect

from core.factories import DocumentFactory, StructureFactory, MessageFactory
from core.models import Structure, Document, Message
from django.contrib.auth import get_user_model

from core.pages import WithDocumentsPage
from core.tests.generic_tests.documents import generic_test_cant_see_document_type_from_other_app
from core.validators import MAX_UPLOAD_SIZE_BYTES
from sv.factories import EvenementFactory
from sv.models import Evenement

User = get_user_model()


def test_can_add_document_to_evenement(live_server, page: Page, mocked_authentification_user: User):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_test_id("documents-add")).to_be_visible()
    page.get_by_test_id("documents-add").click()

    expect(page.locator("#fr-modal-add-doc")).to_be_visible()

    page.locator("#id_nom").fill("Name of the document")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#id_description").fill("Description")
    page.locator("#fr-modal-add-doc").locator("#id_file").set_input_files(
        settings.BASE_DIR / "static/images/marianne.png"
    )
    page.get_by_test_id("documents-send").click()

    assert evenement.documents.count() == 1
    document = evenement.documents.get()

    assert document.document_type == Document.TypeDocument.COMPTE_RENDU_REUNION
    assert document.nom == "Name of the document"
    assert document.description == "Description"
    assert document.created_by == mocked_authentification_user.agent
    assert document.created_by_structure == mocked_authentification_user.agent.structure

    # Check the document is now listed on the page
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Name of the document Information")).to_be_visible()
    expect(page.get_by_text(str(mocked_authentification_user.agent.structure).upper(), exact=True)).to_be_visible()
    expect(page.locator(".fr-tag", has_text=f"{document.get_document_type_display()}")).to_be_visible()


def test_cant_add_document_with_incorrect_extension(live_server, page: Page, mocked_authentification_user: User):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_test_id("documents-add")).to_be_visible()
    page.get_by_test_id("documents-add").click()

    expect(page.locator("#fr-modal-add-doc")).to_be_visible()

    page.locator("#id_nom").fill("Name of the document")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#id_description").fill("Description")
    page.locator("#fr-modal-add-doc").locator("#id_file").set_input_files("scalingo.json")
    page.get_by_test_id("documents-send").click()

    validation_message = page.locator("#fr-modal-add-doc #id_file").evaluate("el => el.validationMessage")
    assert "L'extension du fichier n'est pas autorisé pour le type de document sélectionné" in validation_message
    assert evenement.documents.count() == 0


def test_cant_add_document_with_correct_extension_but_fake_content(
    live_server, page: Page, mocked_authentification_user: User
):
    evenement = EvenementFactory()
    with open("test.csv", mode="w+") as file:
        file.write("<script>alert('Hello');</script>")
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_test_id("documents-add")).to_be_visible()
    page.get_by_test_id("documents-add").click()

    expect(page.locator("#fr-modal-add-doc")).to_be_visible()

    page.locator("#id_nom").fill("Name of the document")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#id_description").fill("Description")
    page.locator("#fr-modal-add-doc").locator("#id_file").set_input_files("test.csv")
    page.get_by_test_id("documents-send").click()

    assert evenement.documents.count() == 0

    expect(page.get_by_text("Une erreur s'est produite lors de l'ajout du document")).to_be_visible()
    expect(page.get_by_text("Type de fichier non autorisé: text/html")).to_be_visible()
    Path("test.csv").unlink()


def test_can_see_and_delete_document_on_evenement(live_server, page: Page, mocked_authentification_user: User):
    evenement = EvenementFactory()
    document = DocumentFactory(nom="Test document", description="", content_object=evenement, is_infected=False)
    evenement.documents.set([document])
    assert evenement.documents.count() == 1

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Test document", exact=True)).to_be_visible()

    page.locator(f'button[aria-controls="fr-modal-{document.id}"].fr-icon-delete-line').click()
    expect(page.locator(f"#fr-modal-{document.id}")).to_be_visible()
    page.get_by_test_id(f"documents-delete-{document.id}").click()

    page.wait_for_timeout(600)
    document = evenement.documents.get()
    assert document.is_deleted is True
    assert document.deleted_by == mocked_authentification_user.agent

    # Document is still displayed
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Test document")).to_be_visible()
    expect(page.get_by_text("Document supprimé")).to_be_visible()


def test_can_edit_document_on_evenement(live_server, page: Page):
    evenement = EvenementFactory()
    document = DocumentFactory(content_object=evenement, nom="Test document", description="My description")
    evenement.documents.set([document])
    assert evenement.documents.count() == 1

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    document_page = WithDocumentsPage(page)
    document_page.open_document_tab()
    expect(document_page.document_title(document.pk)).to_be_visible()
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


def test_can_filter_documents_by_type_on_evenement(live_server, page: Page):
    evenement = EvenementFactory()
    document_1 = DocumentFactory(content_object=evenement, description="", nom="Test document", document_type="autre")
    document_2 = DocumentFactory(content_object=evenement, description="", nom="Ma carto", document_type="cartographie")
    evenement.documents.set([document_1, document_2])

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}#tabpanel-documents-panel")

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).to_be_visible()

    page.locator(".documents__filters #id_document_type").select_option("autre")
    page.get_by_test_id("documents-filter").click()

    assert (
        page.url
        == f"{live_server.url}{evenement.get_absolute_url()}?document_type=autre&created_by_structure=#tabpanel-documents-panel"
    )

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).not_to_be_visible()


def test_can_filter_documents_by_unit_on_evenement(live_server, page: Page, check_select_options):
    evenement = EvenementFactory()
    document_1 = DocumentFactory(nom="Test document", content_object=evenement, description="")
    other_structure = StructureFactory(libelle="Other structure")
    document_2 = DocumentFactory(
        nom="Ma carto", content_object=evenement, description="", created_by_structure=other_structure
    )
    _structure_with_no_document = StructureFactory(libelle="Should not be in the list")
    evenement.documents.set([document_1, document_2])

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}#tabpanel-documents-panel")

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).to_be_visible()

    check_select_options(page, "id_created_by_structure", ["Other structure", "Structure Test"])
    page.locator(".documents__filters #id_created_by_structure").select_option("Structure Test")
    page.get_by_test_id("documents-filter").click()

    assert (
        page.url
        == f"{live_server.url}{evenement.get_absolute_url()}?document_type=&created_by_structure={document_1.created_by_structure.id}#tabpanel-documents-panel"
    )

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).not_to_be_visible()


def test_cant_add_document_if_brouillon(client):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    test_file = SimpleUploadedFile(name="test.pdf", content=b"contenu du fichier test", content_type="application/pdf")
    data = {
        "nom": "Un fichier test",
        "document_type": Document.TypeDocument.AUTRE,
        "description": "Description du fichier test",
        "file": test_file,
        "content_type": ContentType.objects.get_for_model(evenement).pk,
        "object_id": evenement.id,
        "next": evenement.get_absolute_url(),
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


def test_cant_delete_document_if_brouillon(client):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    document = DocumentFactory(content_object=evenement)
    evenement.documents.set([document])

    response = client.post(
        reverse("document-delete", kwargs={"pk": document.pk}),
        data={"next": evenement.get_absolute_url()},
        follow=True,
    )
    document.refresh_from_db()

    assert document.is_deleted is False
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_cant_edit_document_if_brouillon(client):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    document = DocumentFactory(nom="Test document", description="un document", content_object=evenement)
    evenement.documents.set([document])

    response = client.post(
        reverse("document-update", kwargs={"pk": document.pk}),
        data={"next": evenement.get_absolute_url(), "nom": "Nouveau nom", "description": "Nouvelle description"},
        follow=True,
    )
    document.refresh_from_db()

    assert document.nom == "Test document"
    assert document.description == "un document"
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_adding_document_adds_agent_and_structure_contacts(live_server, page: Page, mocked_authentification_user: User):
    """Test que l'ajout d'un document ajoute l'agent et sa structure comme contacts"""
    evenement = EvenementFactory()

    # Ajout du document
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()
    expect(page.locator("#fr-modal-add-doc")).to_be_visible()
    page.locator("#id_nom").fill("Test Document")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#id_description").fill("Description test")
    page.locator("#fr-modal-add-doc").locator("#id_file").set_input_files(
        settings.BASE_DIR / "static/images/marianne.png"
    )
    page.get_by_test_id("documents-send").click()

    # Vérification que le document a été créé
    assert evenement.documents.count() == 1
    document = evenement.documents.get()
    assert document.created_by == mocked_authentification_user.agent
    assert document.created_by_structure == mocked_authentification_user.agent.structure

    # Vérification des contacts dans l'interface
    page.get_by_test_id("contacts").click()

    agents_section = page.locator("[data-testid='contacts-agents']")
    expect(agents_section.get_by_text(str(mocked_authentification_user.agent), exact=True)).to_be_visible()

    structures_section = page.locator("[data-testid='contacts-structures']")
    expect(
        structures_section.get_by_text(str(mocked_authentification_user.agent.structure), exact=True)
    ).to_be_visible()

    # Vérification en base de données
    assert evenement.contacts.filter(agent=mocked_authentification_user.agent).exists()
    assert evenement.contacts.filter(structure=mocked_authentification_user.agent.structure).exists()


def test_adding_multiple_documents_adds_contacts_once(live_server, page: Page, mocked_authentification_user: User):
    """Test que l'ajout de plusieurs documents n'ajoute qu'une fois les contacts"""
    evenement = EvenementFactory()

    # Ajout du premier document
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()
    expect(page.locator("#fr-modal-add-doc")).to_be_visible()
    page.locator("#fr-modal-add-doc #id_nom").fill("Document 1")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#fr-modal-add-doc #id_description").fill("Description 1")
    page.locator("#fr-modal-add-doc #id_file").set_input_files(settings.BASE_DIR / "static/images/marianne.png")
    page.get_by_test_id("documents-send").click()

    # Ajout du second document
    page.get_by_test_id("documents-add").click()
    expect(page.locator("#fr-modal-add-doc")).to_be_visible()
    page.locator("#fr-modal-add-doc #id_nom").fill("Document 2")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#fr-modal-add-doc #id_description").fill("Description 2")
    page.locator("#fr-modal-add-doc #id_file").set_input_files(settings.BASE_DIR / "static/images/marianne.png")
    page.get_by_test_id("documents-send").click()

    # Vérification que les deux documents ont été créés
    assert evenement.documents.count() == 2

    # Vérification des contacts dans l'interface
    page.get_by_test_id("contacts").click()

    # Vérification qu'il n'y a qu'une occurrence de chaque contact
    agents_section = page.locator("[data-testid='contacts-agents']")
    expect(agents_section.get_by_text(str(mocked_authentification_user.agent), exact=True)).to_be_visible()

    structures_section = page.locator("[data-testid='contacts-structures']")
    expect(
        structures_section.get_by_text(str(mocked_authentification_user.agent.structure), exact=True)
    ).to_be_visible()

    # Vérification en base de données
    assert evenement.contacts.filter(agent=mocked_authentification_user.agent).count() == 1
    assert evenement.contacts.filter(structure=mocked_authentification_user.agent.structure).count() == 1


def test_cant_forge_document_edit_of_document_i_cant_see(client):
    evenement = EvenementFactory(createur=Structure.objects.create(libelle="A new structure"))
    document = DocumentFactory(nom="Test document", description="", content_object=evenement)

    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    payload = {
        "nom": "This is mine",
        "document_type": "arrete_prefectoral_ministériel",
        "description": "",
        "pk": document.pk,
        "next": f"/sv/evenement/{evenement.pk}/",
    }
    response = client.post(reverse("document-update", kwargs={"pk": document.pk}), data=payload)

    assert response.status_code == 403
    document.refresh_from_db()
    assert document.nom != "This is mine"


def test_cant_forge_document_updload_on_evenement_i_cant_see(client):
    evenement = EvenementFactory(createur=Structure.objects.create(libelle="A new structure"))
    content_type = ContentType.objects.get_for_model(evenement)

    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    file = SimpleUploadedFile("file.mp4", b"file_content", content_type="video/mp4")
    payload = {
        "nom": "This is mine",
        "document_type": "arrete_prefectoral_ministériel",
        "description": "",
        "file": file,
        "content_type": content_type.pk,
        "object_id": evenement.pk,
        "next": f"/sv/evenement/{evenement.pk}/",
    }
    response = client.post(reverse("document-upload"), data=payload)

    assert response.status_code == 403
    evenement.refresh_from_db()
    assert evenement.documents.count() == 0


def test_cant_delete_document_of_evenement_i_cant_see(client):
    evenement = EvenementFactory(createur=Structure.objects.create(libelle="A new structure"))
    document = DocumentFactory(content_object=evenement)
    evenement.documents.set([document])

    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    payload = {"pk": document.pk, "next": f"/sv/evenement/{evenement.pk}/"}
    response = client.post(reverse("document-delete", kwargs={"pk": document.pk}), data=payload)

    assert response.status_code == 403
    evenement.refresh_from_db()
    assert evenement.documents.filter(is_deleted=True).count() == 0
    assert evenement.documents.filter(is_deleted=False).count() == 1


def test_add_document_is_scanned_by_antivirus(live_server, page: Page, mocked_authentification_user: User, settings):
    settings.BYPASS_ANTIVIRUS = False
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_test_id("documents-add")).to_be_visible()
    page.get_by_test_id("documents-add").click()

    expect(page.locator("#fr-modal-add-doc")).to_be_visible()

    page.locator("#id_nom").fill("Name of the document")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#id_description").fill("Description")
    page.locator("#fr-modal-add-doc").locator("#id_file").set_input_files(
        settings.BASE_DIR / "static/images/marianne.png"
    )
    page.get_by_test_id("documents-send").click()

    assert evenement.documents.count() == 1
    document = evenement.documents.get()

    assert document.document_type == Document.TypeDocument.COMPTE_RENDU_REUNION
    assert document.nom == "Name of the document"
    assert document.description == "Description"
    assert document.created_by == mocked_authentification_user.agent
    assert document.created_by_structure == mocked_authentification_user.agent.structure
    assert document.is_infected is None

    # Check the document is not listed on the page
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Name of the document Information")).to_be_visible()
    expect(page.get_by_text(str(mocked_authentification_user.agent.structure).upper(), exact=True)).to_be_visible()
    expect(page.locator(".fr-tag", has_text=f"{document.get_document_type_display()}")).to_be_visible()
    expect(page.locator(f'[href*="{document.file.url}"]')).not_to_be_visible()
    expect(page.get_by_text("Analyse antivirus", exact=True)).to_be_visible()

    document.is_infected = True
    document.save()

    page.reload()
    # Check the document is not listed on the page
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Name of the document Information")).not_to_be_visible()
    expect(page.get_by_text(str(mocked_authentification_user.agent.structure).upper(), exact=True)).not_to_be_visible()
    expect(page.locator(".fr-tag", has_text=f"{document.get_document_type_display()}")).not_to_be_visible()
    expect(page.locator(f'[href*="{document.file.url}"]')).not_to_be_visible()

    document.is_infected = False
    document.save()

    page.reload()
    # Check the document is now listed on the page
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Name of the document Information")).to_be_visible()
    expect(page.get_by_text(str(mocked_authentification_user.agent.structure).upper(), exact=True)).to_be_visible()
    expect(page.locator(".fr-tag", has_text=f"{document.get_document_type_display()}")).to_be_visible()
    expect(page.locator(f'[href*="{document.file.url}"]')).to_be_visible()


def test_document_upload_exceeding_max_size_shows_validation_error_and_prevents_creation(live_server, page: Page):
    # Créer un fichier temporaire CSV de 16Mo
    file_size = 16 * 1024 * 1024
    fd, temp_path = tempfile.mkstemp(suffix=".csv")
    os.truncate(fd, file_size)
    os.close(fd)

    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()

    # Vérifier que le champ de fichier a la bonne valeur data-max-size
    file_input = page.locator("#fr-modal-add-doc #id_file")
    max_size_attr = file_input.get_attribute("data-max-size")
    assert int(max_size_attr) == MAX_UPLOAD_SIZE_BYTES

    # Télécharger le fichier trop volumineux
    page.locator("#id_nom").fill("Document trop volumineux")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#id_description").fill("Test validation taille")
    page.locator("#fr-modal-add-doc").locator("#id_file").set_input_files(temp_path)
    page.get_by_test_id("documents-send").click()

    # Vérifier le message de validation
    validation_message = file_input.evaluate("el => el.validationMessage")
    assert "Le fichier est trop volumineux (maximum 15 Mo autorisés)" in validation_message

    os.unlink(temp_path)

    evenement.refresh_from_db()
    assert evenement.documents.count() == 0


def test_document_upload_with_missing_max_size_shows_configuration_error(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()

    # Supprimer l'attribut data-max-size du champ de fichier
    file_input = page.locator("#fr-modal-add-doc #id_file")
    page.evaluate("""() => {
        const fileInput = document.querySelector('#fr-modal-add-doc #id_file');
        fileInput.removeAttribute('data-max-size');
    }""")

    page.locator("#id_nom").fill("Test configuration manquante")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#id_description").fill("Test attribut manquant")
    file_input.set_input_files(settings.BASE_DIR / "static/images/marianne.png")

    validation_message = file_input.evaluate("el => el.validationMessage")
    assert "Erreur de configuration: limite de taille non définie" in validation_message

    page.get_by_test_id("documents-send").click()
    evenement.refresh_from_db()
    assert evenement.documents.count() == 0


def test_document_upload_with_invalid_max_size_shows_configuration_error(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()

    # Définir une valeur non numérique pour data-max-size
    file_input = page.locator("#fr-modal-add-doc #id_file")
    page.evaluate("""() => {
        const fileInput = document.querySelector('#fr-modal-add-doc #id_file');
        fileInput.setAttribute('data-max-size', 'not-a-number');
    }""")

    page.locator("#id_nom").fill("Test configuration invalide")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#id_description").fill("Test attribut invalide")
    file_input.set_input_files(settings.BASE_DIR / "static/images/marianne.png")

    validation_message = file_input.evaluate("el => el.validationMessage")
    assert "Erreur de configuration: limite de taille invalide" in validation_message

    page.get_by_test_id("documents-send").click()
    evenement.refresh_from_db()
    assert evenement.documents.count() == 0


def test_cant_see_add_document_btn_if_evenement_is_cloture(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_test_id("documents-add")).not_to_be_visible()


def test_cant_forge_upload_document_if_evenement_is_cloture(client):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    file = SimpleUploadedFile("file.png", b"file_content", content_type="image/png")
    payload = {
        "nom": "This is mine",
        "document_type": "arrete_prefectoral_ministériel",
        "description": "",
        "file": file,
        "content_type": ContentType.objects.get_for_model(evenement).pk,
        "object_id": evenement.pk,
        "next": f"/sv/evenement/{evenement.pk}/",
    }

    response = client.post(reverse("document-upload"), data=payload)

    assert response.status_code == 403
    evenement.refresh_from_db()
    assert evenement.documents.count() == 0


def test_cant_see_update_document_btn_if_evenement_is_cloture(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    document = DocumentFactory(content_object=evenement)
    evenement.documents.set([document])

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.locator(f'.fr-btns-group button[aria-controls="fr-modal-edit-{document.id}"]')).not_to_be_visible()


def test_cant_forge_update_document_if_evenement_is_cloture(client):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    document = DocumentFactory(nom="Test document", description="", content_object=evenement)
    evenement.documents.set([document])

    payload = {
        "nom": "This is mine",
        "document_type": "arrete_prefectoral_ministériel",
        "description": "",
        "pk": document.pk,
        "next": f"/sv/evenement/{evenement.pk}/",
    }
    response = client.post(reverse("document-update", kwargs={"pk": document.pk}), data=payload)

    assert response.status_code == 403
    document.refresh_from_db()
    assert document.nom != "This is mine"


def test_cant_see_delete_document_btn_if_evenement_is_cloture(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    document = DocumentFactory(content_object=evenement)
    evenement.documents.set([document])

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_test_id(f"documents-delete-{document.id}")).not_to_be_visible()


def test_cant_forge_delete_document_if_evenement_is_cloture(client):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    document = DocumentFactory(content_object=evenement)
    evenement.documents.set([document])

    payload = {"pk": document.pk, "next": f"/sv/evenement/{evenement.pk}/"}
    response = client.post(reverse("document-delete", kwargs={"pk": document.pk}), data=payload)

    assert response.status_code == 403
    evenement.refresh_from_db()
    assert evenement.documents.filter(is_deleted=True).count() == 0
    assert evenement.documents.filter(is_deleted=False).count() == 1


def test_cant_see_download_document_btn_if_evenement_is_cloture(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    document = DocumentFactory(content_object=evenement)
    evenement.documents.set([document])

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.locator(f'[href*="{document.file.url}"]')).not_to_be_visible()


def test_change_document_type_to_cartographie_updates_accept_attribute_and_infos_span(live_server, page: Page):
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.CARTOGRAPHIE)

    file_input = page.locator("#fr-modal-add-doc #id_file")
    accept_attr = file_input.get_attribute("accept")
    assert accept_attr == ".png,.jpg,.jpeg"
    assert page.locator("#fr-modal-add-doc #allowed-extensions-list").inner_text() == "png, jpg, jpeg"


@pytest.mark.django_db
def test_can_upload_document_with_allowed_extension_for_cartographie(live_server, page: Page):
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()
    page.locator("#id_nom").fill("Test upload doc cartographie")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.CARTOGRAPHIE)
    page.locator("#fr-modal-add-doc #id_file").set_input_files(settings.BASE_DIR / "static/images/marianne.png")
    page.get_by_test_id("documents-send").click()

    evenement.refresh_from_db()
    assert evenement.documents.count() == 1


@pytest.mark.django_db
def test_cant_upload_document_with_not_allowed_extension_for_cartographie(live_server, page: Page):
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()
    page.locator("#id_nom").fill("Test upload doc cartographie")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.CARTOGRAPHIE)

    file_input = page.locator("#fr-modal-add-doc #id_file")
    page.locator("#fr-modal-add-doc #id_file").set_input_files("scalingo.json")
    page.get_by_test_id("documents-send").click()

    validation_message = file_input.evaluate("el => el.validationMessage")
    assert "L'extension du fichier n'est pas autorisé pour le type de document sélectionné" in validation_message
    evenement.refresh_from_db()
    assert evenement.documents.count() == 0


@pytest.mark.django_db
def test_cant_upload_document_with_missing_accept_allowed_extensions_shows_configuration_error(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()

    page.evaluate("""() => {
        const fileInput = document.querySelector('#fr-modal-add-doc #id_file');
        fileInput.removeAttribute('data-accept-allowed-extensions');
    }""")

    page.locator("#id_nom").fill("Test configuration manquante")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    file_input = page.locator("#fr-modal-add-doc #id_file")
    file_input.set_input_files(settings.BASE_DIR / "static/images/marianne.png")

    expect(page.get_by_test_id("documents-send")).to_be_disabled()
    evenement.refresh_from_db()
    assert evenement.documents.count() == 0


@pytest.mark.django_db
def test_cant_upload_document_with_missing_accept_for_cartographie_shows_configuration_error(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()

    page.evaluate("""() => {
        const fileInput = document.querySelector('#fr-modal-add-doc #id_file');
        fileInput.setAttribute('data-accept-allowed-extensions', '{"default": ".pdf"}');
    }""")

    page.locator("#id_nom").fill("Test configuration manquante pour cartographie")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.CARTOGRAPHIE)
    file_input = page.locator("#fr-modal-add-doc #id_file")
    file_input.set_input_files("scalingo.json")

    expect(page.get_by_test_id("documents-send")).to_be_disabled()
    evenement.refresh_from_db()
    assert evenement.documents.count() == 0


@pytest.mark.django_db
def test_cant_upload_document_with_incompatible_extension_for_cartographie(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()

    page.locator("#id_nom").fill("Test upload doc cartographie")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    file_input = page.locator("#fr-modal-add-doc #id_file")
    file_input.set_input_files("fake_contacts.csv")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.CARTOGRAPHIE)
    page.get_by_test_id("documents-send").click()

    validation_message = file_input.evaluate("el => el.validationMessage")
    assert "L'extension du fichier n'est pas autorisé pour le type de document sélectionné" in validation_message
    evenement.refresh_from_db()
    assert evenement.documents.count() == 0


def test_document_name_length_validation(live_server, page: Page, mocked_authentification_user: User):
    evenement = EvenementFactory()
    long_name = "a" * 257

    # Test pour le formulaire d'ajout
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    page.get_by_test_id("documents-add").click()
    page.locator("#id_nom").fill(long_name)
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#id_description").fill("Description test")
    page.locator("#fr-modal-add-doc").locator("#id_file").set_input_files(
        settings.BASE_DIR / "static/images/marianne.png"
    )
    page.get_by_test_id("documents-send").click()

    assert evenement.documents.count() == 1
    document = evenement.documents.get()
    assert len(document.nom) == 256
    assert document.is_infected is False

    # Test pour le formulaire de mise à jour
    page.locator(f'.fr-btns-group button[aria-controls="fr-modal-edit-{document.id}"]').click()
    expect(page.locator(f"#fr-modal-edit-{document.id}")).to_be_visible()
    page.locator(f"#fr-modal-edit-{document.id} #id_nom").fill(long_name)
    page.get_by_test_id(f"documents-edit-{document.pk}").click()
    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-documents-panel")
    document.refresh_from_db()
    assert len(document.nom) == 256


def test_can_edit_document_from_message(live_server, page: Page):
    evenement = EvenementFactory()
    message = MessageFactory(content_object=evenement, message_type=Message.MESSAGE)
    document = DocumentFactory(nom="Test document", description="", content_object=message, is_infected=False)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}#tabpanel-documents-panel")
    page.locator(f'.fr-btns-group button[aria-controls="fr-modal-edit-{document.id}"]').click()
    page.locator(f"#fr-modal-edit-{document.id} #id_nom").fill("New name")
    page.locator(f"#fr-modal-edit-{document.id} #id_description").fill("un commentaire")
    page.get_by_test_id(f"documents-edit-{document.pk}").click()
    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-documents-panel")

    document.refresh_from_db()
    assert document.nom == "New name"
    assert document.description == "un commentaire"


def test_cant_see_document_from_message_with_brouillon_status(live_server, page: Page):
    evenement = EvenementFactory()
    message = MessageFactory(content_object=evenement, message_type=Message.MESSAGE, status=Message.Status.BROUILLON)
    DocumentFactory(nom="Test document", content_object=message)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}#tabpanel-documents-panel")
    expect(page.locator("#tabpanel-documents-panel").get_by_text("Test document")).not_to_be_visible()


def test_cant_see_document_type_from_other_app(live_server, page: Page, check_select_options_from_element):
    evenement = EvenementFactory()
    generic_test_cant_see_document_type_from_other_app(live_server, page, check_select_options_from_element, evenement)
