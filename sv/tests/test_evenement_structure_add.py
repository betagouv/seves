import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import expect

from core.factories import StructureFactory, AgentFactory, ContactStructureFactory
from core.models import Structure, Contact
from sv.factories import EvenementFactory
from sv.models import Evenement


@pytest.fixture
def contacts_structure():
    return ContactStructureFactory.create_batch(2, with_one_active_agent=True)


@pytest.mark.django_db
def test_add_structure_form(live_server, page, contacts_structure):
    """Test l'affichage du formulaire d'ajout de structure"""
    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()

    expect(page.get_by_role("link", name="Retour à l'évenement")).to_be_visible()
    expect(page.get_by_role("heading", name="Ajouter une structure")).to_be_visible()
    expect(page.get_by_text("En :")).to_be_visible()
    expect(page.get_by_text(contacts_structure[0].structure.niveau1)).to_be_visible()
    expect(page.get_by_text(contacts_structure[1].structure.niveau1)).to_be_visible()
    expect(page.get_by_role("button", name="Rechercher")).to_be_visible()


@pytest.mark.django_db
def test_cant_forge_url_to_create_open_redirect_add_structure_form(live_server, page, contacts_structure):
    evenement = EvenementFactory()
    content_type = ContentType.objects.get_for_model(evenement)
    url = (
        reverse("contact-add-form")
        + f"?fiche_id={evenement.pk}&content_type_id={content_type.pk}&next=https://google.fr"
    )
    page.goto(f"{live_server.url}/{url}")

    expect(page.get_by_role("link", name="Retour à l'évenement")).to_have_attribute(
        "href", evenement.get_absolute_url()
    )


@pytest.mark.django_db
def test_add_structure_form_hides_empty_emails(live_server, page):
    ContactStructureFactory(structure__niveau1="Level 1", with_one_active_agent=True)
    ContactStructureFactory(structure__niveau1="Level 2", with_one_active_agent=True, email="")
    ContactStructureFactory(structure__niveau1="Level 3", with_one_active_agent=True)

    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()

    expect(page.get_by_text("Level 1")).to_be_visible()
    expect(page.get_by_text("Level 2")).not_to_be_visible()
    expect(page.get_by_text("Level 3")).to_be_visible()


@pytest.mark.django_db
def test_add_structure_form_hides_structure_without_active_user(live_server, page, contacts_structure):
    visible_structure = StructureFactory()
    _inactive_agent = AgentFactory(structure=visible_structure, user__is_active=False)
    active_agent = AgentFactory(structure=visible_structure)
    active_agent.user.is_active = True
    active_agent.user.save()

    unvisible_structure = StructureFactory()
    AgentFactory(structure=unvisible_structure, user__is_active=False)
    AgentFactory(structure=unvisible_structure, user__is_active=False)

    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()

    expect(page.get_by_text(visible_structure.niveau1)).to_be_visible()
    expect(page.get_by_text(unvisible_structure.niveau1)).not_to_be_visible()


@pytest.mark.django_db
def test_add_structure_form_service_account_is_hidden(live_server, page):
    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    expect(page.get_by_text("service_account")).not_to_be_visible()


def test_add_structure_form_back_to_evenement(live_server, page):
    """Test le lien de retour vers l'évenement"""
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    page.get_by_role("link", name="Retour à l'évenement").click()

    expect(page).to_have_url(f"{live_server.url}{evenement.get_absolute_url()}")


@pytest.mark.django_db
def test_structure_niveau2_are_visible_after_select_structure_niveau1(live_server, page, contacts_structure):
    """Test l'affichage des structures de niveau 2 suite à la selection d'une structure de niveau 1"""
    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()

    for contact in contacts_structure:
        page.get_by_text(contact.structure.niveau1).click()
        page.get_by_role("button", name="Rechercher").click()
        expect(page.get_by_text(contact.structure.libelle)).to_be_visible()


@pytest.mark.django_db
def test_structure_niveau2_without_emails_are_not_visible_after_select_structure_niveau1(live_server, page):
    ContactStructureFactory(structure__niveau1="Level 1", structure__libelle="Foo", with_one_active_agent=True)
    ContactStructureFactory(
        structure__niveau1="Level 1", structure__libelle="Bar", with_one_active_agent=True, email=""
    )
    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()

    page.get_by_text("Level 1").click()
    page.get_by_role("button", name="Rechercher").click()
    expect(page.get_by_text("Foo")).to_be_visible()
    expect(page.get_by_text("Bar")).not_to_be_visible()


@pytest.mark.django_db
def test_add_structure_to_an_evenement(live_server, page, contacts_structure):
    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    page.get_by_text(contacts_structure[0].structure.niveau1).click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(contacts_structure[0].structure.libelle).click()
    page.get_by_role("button", name="Ajouter les structures sélectionnées").click()
    expect(page.get_by_text("La structure a été ajoutée avec succès.")).to_be_visible()
    expect(page.locator("p").filter(has_text=contacts_structure[0].structure.libelle)).to_be_visible()


@pytest.mark.django_db
def test_add_multiple_structures_to_an_evenement(live_server, page):
    contact1 = ContactStructureFactory(structure__niveau1="AC", with_one_active_agent=True)
    contact2 = ContactStructureFactory(structure__niveau1="AC", with_one_active_agent=True)

    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    page.get_by_text(contact1.structure.niveau1, exact=True).click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(contact1.structure.libelle).click()
    page.get_by_text(contact2.structure.libelle).click()
    page.get_by_role("button", name="Ajouter les structures sélectionnées").click()

    expect(page.get_by_text("Les 2 structures ont été ajoutées avec succès.")).to_be_visible()
    expect(page.locator(".bloc-commun__panel--contacts")).to_contain_text(contact1.structure.libelle)
    expect(page.locator(".bloc-commun__panel--contacts")).to_contain_text(contact2.structure.libelle)


@pytest.mark.django_db
def test_no_structure_selected(live_server, page, contacts_structure):
    """Test l'affichage d'un message d'erreur si aucune structure n'est sélectionné lors de l'envoi du formulaire"""
    page.goto(f"{live_server.url}/{EvenementFactory().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    page.get_by_text(contacts_structure[0].structure.niveau1).click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter les structures sélectionnées").click()
    expect(page.get_by_text("Veuillez sélectionner au moins une structure")).to_be_visible()


@pytest.mark.django_db
def test_add_structure_form_back_to_evenement_after_select_structure_niveau1(live_server, page, contacts_structure):
    """Test le retour à l'événement après avoir sélectionné une structure de niveau 1"""
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter une structure").click()
    page.get_by_text(contacts_structure[0].structure.niveau1).click()
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("link", name="Retour à l'évenement").click()

    expect(page).to_have_url(f"{live_server.url}{evenement.get_absolute_url()}")


@pytest.mark.django_db
def test_cant_access_structure_selection_add_form_if_evenement_brouillon(live_server, page):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    content_type = ContentType.objects.get_for_model(evenement)
    page.goto(
        f"{live_server.url}/{reverse('structure-selection-add-form')}?fiche_id={evenement.id}&content_type_id={content_type.id}&next={evenement.get_absolute_url()}"
    )
    expect(page.get_by_text("Action impossible car la fiche est en brouillon")).to_be_visible()


@pytest.mark.django_db
def test_cant_post_structure_selection_add_form_if_evenement_brouillon(client, mocked_authentification_user):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    response = client.post(
        reverse("structure-selection-add-form"),
        data={
            "fiche_id": evenement.id,
            "next": evenement.get_absolute_url(),
            "content_type_id": ContentType.objects.get_for_model(evenement).id,
            "structure_niveau1": evenement.createur,
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


@pytest.mark.django_db
def test_cant_post_structure_add_form_if_evenement_brouillon(client, mocked_authentification_user):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    structure = Structure.objects.create(
        niveau1=evenement.createur, niveau2="une autre structure", libelle="une autre structure"
    )
    contact = Contact.objects.create(structure=structure)

    response = client.post(
        reverse("structure-add"),
        data={
            "content_type_id": ContentType.objects.get_for_model(evenement).id,
            "fiche_id": evenement.id,
            "next": evenement.get_absolute_url(),
            "structure_selected": evenement.createur,
            "contacts": [contact],
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"
