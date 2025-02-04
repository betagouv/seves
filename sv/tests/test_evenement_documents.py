from pathlib import Path

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from model_bakery import baker
from playwright.sync_api import Page, expect

from core.models import Structure, Document
from django.contrib.auth import get_user_model

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
    page.locator("#fr-modal-add-doc").locator("#id_file").set_input_files("static/images/marianne.png")
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
    expect(page.locator(".document__details--type", has_text=f"{document.get_document_type_display()}")).to_be_visible()


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

    assert evenement.documents.count() == 0

    expect(page.get_by_text("Une erreur s'est produite lors de l'ajout du document")).to_be_visible()
    expect(
        page.get_by_text(
            "L'extension de fichier « json » n’est pas autorisée. Les extensions autorisées sont : png, jpg, jpeg, gif, pdf, doc, docx, xls, xlsx, odt, ods, csv, qgs, qgz."
        )
    ).to_be_visible()


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


def test_can_see_and_delete_document_on_evenement(
    live_server, page: Page, mocked_authentification_user: User, document_recipe
):
    evenement = EvenementFactory()
    document = document_recipe().make(nom="Test document", description="")
    evenement.documents.set([document])
    assert evenement.documents.count() == 1

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Test document", exact=True)).to_be_visible()

    page.locator(f'a[aria-controls="fr-modal-{document.id}"]').click()
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


def test_can_edit_document_on_evenement(live_server, page: Page, document_recipe):
    evenement = EvenementFactory()
    document = document_recipe().make(nom="Test document", description="My description")
    evenement.documents.set([document])
    assert evenement.documents.count() == 1

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()

    expect(page.get_by_text("Test document Information")).to_be_visible()

    page.locator(f'a[aria-controls="fr-modal-edit-{document.id}"]').click()
    expect(page.locator(f"#fr-modal-edit-{document.id}")).to_be_visible()

    page.locator(f"#fr-modal-edit-{document.id} #id_nom").fill("New name")
    page.locator(f"#fr-modal-edit-{document.id} #id_description").fill("")
    page.get_by_test_id(f"documents-edit-{document.pk}").click()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-documents-panel")

    document = evenement.documents.get()
    assert document.nom == "New name"
    assert document.description == ""

    page.get_by_test_id("documents").click()
    expect(page.get_by_text("New name", exact=True)).to_be_visible()


def test_can_filter_documents_by_type_on_evenement(live_server, page: Page, document_recipe):
    evenement = EvenementFactory()
    document_1 = document_recipe().make(nom="Test document", document_type="autre", description="")
    document_2 = document_recipe().make(nom="Ma carto", document_type="cartographie", description="")
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


def test_can_filter_documents_by_unit_on_evenement(live_server, page: Page, document_recipe):
    evenement = EvenementFactory()
    document_1 = document_recipe().make(nom="Test document", document_type="autre", description="")
    other_structure = baker.make(Structure)
    document_2 = document_recipe().make(
        nom="Ma carto", document_type="cartographie", description="", created_by_structure=other_structure
    )
    _structure_with_no_document = baker.make(Structure, libelle="Should not be in the list")
    evenement.documents.set([document_1, document_2])

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}#tabpanel-documents-panel")

    expect(page.get_by_text("Test document", exact=True)).to_be_visible()
    expect(page.get_by_text("Ma carto", exact=True)).to_be_visible()

    assert page.locator(".documents__filters #id_created_by_structure").all_inner_texts() == [
        "\n".join(["---------", "Structure Test"])
    ]
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


def test_cant_delete_document_if_brouillon(client, document_recipe):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    document = document_recipe().make(nom="Test document", description="un document")
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


def test_cant_edit_document_if_brouillon(client, document_recipe):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    document = document_recipe().make(nom="Test document", description="un document")
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
    page.locator("#fr-modal-add-doc").locator("#id_file").set_input_files("static/images/marianne.png")
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
    page.locator("#fr-modal-add-doc #id_file").set_input_files("static/images/marianne.png")
    page.get_by_test_id("documents-send").click()

    # Ajout du second document
    page.get_by_test_id("documents-add").click()
    expect(page.locator("#fr-modal-add-doc")).to_be_visible()
    page.locator("#fr-modal-add-doc #id_nom").fill("Document 2")
    page.locator("#fr-modal-add-doc #id_document_type").select_option(Document.TypeDocument.COMPTE_RENDU_REUNION)
    page.locator("#fr-modal-add-doc #id_description").fill("Description 2")
    page.locator("#fr-modal-add-doc #id_file").set_input_files("static/images/marianne.png")
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


def test_cant_forge_document_edit_of_document_i_cant_see(client, document_recipe):
    evenement = EvenementFactory(createur=Structure.objects.create(libelle="A new structure"))
    document = document_recipe().make(nom="Test document", description="")
    evenement.documents.set([document])

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


def test_cant_delete_document_of_evenement_i_cant_see(client, document_recipe):
    evenement = EvenementFactory(createur=Structure.objects.create(libelle="A new structure"))
    document = document_recipe().make(nom="Test document", description="")
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
    page.locator("#fr-modal-add-doc").locator("#id_file").set_input_files("README.md")
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
    expect(page.locator(".document__details--type", has_text=f"{document.get_document_type_display()}")).to_be_visible()
    expect(page.locator(f'[href*="{document.file.url}"]')).not_to_be_visible()
    expect(page.get_by_text("En cours d'analyse antivirus")).to_be_visible()

    document.is_infected = True
    document.save()

    page.reload()
    # Check the document is not listed on the page
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Name of the document Information")).not_to_be_visible()
    expect(page.get_by_text(str(mocked_authentification_user.agent.structure).upper(), exact=True)).not_to_be_visible()
    expect(
        page.locator(".document__details--type", has_text=f"{document.get_document_type_display()}")
    ).not_to_be_visible()
    expect(page.locator(f'[href*="{document.file.url}"]')).not_to_be_visible()

    document.is_infected = False
    document.save()

    page.reload()
    # Check the document is now listed on the page
    page.get_by_test_id("documents").click()
    expect(page.get_by_text("Name of the document Information")).to_be_visible()
    expect(page.get_by_text(str(mocked_authentification_user.agent.structure).upper(), exact=True)).to_be_visible()
    expect(page.locator(".document__details--type", has_text=f"{document.get_document_type_display()}")).to_be_visible()
    expect(page.locator(f'[href*="{document.file.url}"]')).to_be_visible()
