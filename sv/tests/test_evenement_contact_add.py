import pytest
from django.contrib.contenttypes.models import ContentType
from django.utils.http import urlencode
from playwright.sync_api import expect
from django.urls import reverse

from core.constants import MUS_STRUCTURE
from core.factories import ContactAgentFactory, ContactStructureFactory, StructureFactory
from core.models import Contact, Structure, Agent
from sv.factories import EvenementFactory
from sv.models import Evenement


@pytest.fixture
def contact(db):
    return ContactAgentFactory(with_active_agent=True)


@pytest.fixture
def contacts(db):
    ContactAgentFactory.create_batch(2)

    # création de la structure MUS et de deux contacts de type Agent associés
    structure = StructureFactory(libelle=MUS_STRUCTURE)
    return ContactAgentFactory.create_batch(2, agent__structure=structure, with_active_agent=True)


def test_add_contact_form(live_server, page, mocked_authentification_user):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()

    expect(page.get_by_role("link", name="Retour à l'évenement")).to_be_visible()
    expect(page.get_by_role("heading", name="Ajouter un agent")).to_be_visible()
    expect(page.get_by_text("Structure", exact=True)).to_be_visible()
    expect(page.get_by_text(mocked_authentification_user.agent.structure.libelle).nth(1)).to_be_visible()
    expect(page.get_by_role("button", name="Rechercher")).to_be_visible()


@pytest.mark.django_db
def test_cant_forge_url_to_create_open_redirect_add_contact_form(live_server, page):
    evenement = EvenementFactory()
    content_type = ContentType.objects.get_for_model(evenement)
    url = (
        reverse("structure-selection-add-form")
        + f"?fiche_id={evenement.pk}&content_type_id={content_type.pk}&next=https://google.fr"
    )
    page.goto(f"{live_server.url}/{url}")

    expect(page.get_by_role("link", name="Retour à l'évenement")).to_have_attribute(
        "href", evenement.get_absolute_url()
    )


def test_cant_access_add_contact_form_if_evenement_brouillon(live_server, page):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    content_type = ContentType.objects.get_for_model(evenement)
    page.goto(
        f"{live_server.url}/{reverse('contact-add-form')}?fiche_id={evenement.id}&content_type_id={content_type.id}&next={evenement.get_absolute_url()}"
    )
    expect(page.get_by_text("Action impossible car la fiche est en brouillon")).to_be_visible()


def test_add_contact_form_back_to_evenement(live_server, page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    page.get_by_role("link", name="Retour à l'évenement").click()

    expect(page).to_have_url(f"{live_server.url}{evenement.get_absolute_url()}")


@pytest.mark.django_db
def test_structure_list(live_server, page):
    """Test que la liste des structures soit bien dans le contexte du formulaire d'ajout de contact"""
    Contact.objects.all().delete()
    Agent.objects.all().delete()
    Structure.objects.all().delete()

    for i in range(0, 3):
        ContactAgentFactory(agent__structure__libelle=f"Structure {i + 1}", with_active_agent=True)
    assert Structure.objects.count() == 3

    evenement = EvenementFactory(createur=Structure.objects.first())
    url = f"{reverse('contact-add-form')}?{urlencode({'fiche_id': evenement.pk, 'content_type_id': ContentType.objects.get_for_model(evenement).id, 'next': evenement.get_absolute_url()})}"
    page.goto(f"{live_server.url}{url}")

    page.query_selector(".choices").click()
    page.wait_for_selector("input:focus", state="visible", timeout=2_000)
    page.locator("*:focus").fill("Structure")
    for i in range(0, 3):
        expect(page.get_by_role("option", name=f"Structure {i + 1}", exact=True)).to_be_visible()


def test_add_contact_form_select_structure(live_server, page, contacts, choice_js_fill):
    """Test l'affichage des contacts dans le formulaire de sélection suite à la selection d'une structure"""
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", "MUS", "MUS")
    page.get_by_role("button", name="Rechercher").click()
    contact1 = contacts[0]
    contact2 = contacts[1]
    expect(page.get_by_text(f"{contact1.agent.nom}")).to_be_visible()
    expect(page.get_by_text(f"{contact1.agent.nom}")).to_contain_text(f"{contact1.agent.nom} {contact1.agent.prenom}")
    expect(page.get_by_text(f"{contact2.agent.nom}")).to_be_visible()
    expect(page.get_by_text(f"{contact2.agent.nom}")).to_contain_text(f"{contact2.agent.nom} {contact2.agent.prenom}")


def test_cant_add_contact_form_select_structure_if_evenement_brouillon(client):
    """Test que si un événement est en visibilité brouillon, on ne peut pas afficher des contacts dans le formulaire de sélection suite à la selection d'une structure"""
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    response = client.post(
        reverse("contact-add-form"),
        data={
            "fiche_id": evenement.id,
            "structure": evenement.createur,
            "next": evenement.get_absolute_url(),
            "content_type_id": ContentType.objects.get_for_model(evenement).id,
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_add_contact_to_an_evenement(live_server, page, contacts, choice_js_fill):
    evenement = EvenementFactory()
    contact1 = contacts[0]
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", "MUS", "MUS")
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(f"{contact1.agent.nom} {contact1.agent.prenom}").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()
    page.get_by_role("tab", name="Contacts").click()

    expect(page.get_by_text("Le contact a été ajouté avec succès.")).to_be_visible()
    expect(page.locator(".fr-card__content")).to_be_visible()


def test_cant_add_inactive_contact_to_an_evenement(live_server, page, contacts, choice_js_fill):
    contact1 = contacts[0]
    user = contact1.agent.user
    user.is_active = False
    user.save()

    evenement = EvenementFactory()
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", "MUS", "MUS")
    page.get_by_role("button", name="Rechercher").click()
    expect(page.get_by_text(f"{contact1.agent.nom} {contact1.agent.prenom}")).not_to_be_visible()
    expect(page.get_by_text(f"{contacts[1].agent.nom} {contacts[1].agent.prenom}")).to_be_visible()


def test_add_multiple_contacts_to_an_evenement(live_server, page, contacts, choice_js_fill):
    evenement = EvenementFactory()
    contact1 = contacts[0]
    contact2 = contacts[1]
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", "MUS", "MUS")
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(f"{contact1.agent.nom} {contact1.agent.prenom}").click()
    page.get_by_text(f"{contact2.agent.nom} {contact2.agent.prenom}").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()

    expect(page.get_by_text("Les 2 contacts ont été ajoutés avec succès.")).to_be_visible()
    page.get_by_role("tab", name="Contacts").click()
    expect(page.locator(".fr-card__content").first).to_be_visible()
    expect(page.locator("div:nth-child(2) > .fr-card > .fr-card__body > .fr-card__content")).to_be_visible()


def test_no_contact_selected(live_server, page, contact, choice_js_fill):
    """Test l'affichage d'un message d'erreur si aucun contact n'est sélectionné"""
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", contact.agent.structure.libelle, contact.agent.structure.libelle)
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()

    expect(page.get_by_text("Veuillez sélectionner au")).to_be_visible()
    expect(page.locator("#form-selection")).to_contain_text("Veuillez sélectionner au moins un contact")


def test_add_contact_form_back_to_evenement_after_select_structure(live_server, page, contact, choice_js_fill):
    """Test le lien de retour vers l'événement après la selection d'une structure et l'affichage des contacts associés"""
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", contact.agent.structure.libelle, contact.agent.structure.libelle)
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("link", name="Retour à l'évenement").click()

    expect(page).to_have_url(f"{live_server.url}{evenement.get_absolute_url()}")


def test_add_contact_form_back_to_fiche_after_error_message(live_server, page, contact, choice_js_fill):
    """Test le lien de retour vers l'événement après l'affichage du message d'erreur si aucun contact n'est sélectionné"""
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", contact.agent.structure.libelle, contact.agent.structure.libelle)
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()
    page.get_by_role("link", name="Retour à l'évenement").click()

    expect(page).to_have_url(f"{live_server.url}{evenement.get_absolute_url()}")


def test_cant_add_contact_if_evenement_brouillon(client, contact):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    response = client.post(
        reverse("contact-add-form-select-agents"),
        data={
            "structure": contact.agent.structure.id,
            "contacts": [contact.id],
            "content_type_id": ContentType.objects.get_for_model(evenement).id,
            "fiche_id": evenement.id,
            "next": evenement.get_absolute_url(),
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_cant_delete_contact_if_evenement_brouillon(client, contact):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    evenement.contacts.set([contact])

    response = client.post(
        reverse("contact-delete"),
        data={
            "content_type_pk": ContentType.objects.get_for_model(evenement).id,
            "fiche_pk": evenement.id,
            "pk": contact.id,
            "next": evenement.get_absolute_url(),
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_add_agent_contact_adds_structure_contact(live_server, page, choice_js_fill):
    """Test que l'ajout d'un contact agent ajoute automatiquement le contact de sa structure"""
    structure_contact = ContactStructureFactory()
    agent_contact = ContactAgentFactory(agent__structure=structure_contact.structure)
    agent_contact.agent.user.is_active = True
    agent_contact.agent.user.save()
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(
        page, ".choices__list--single", structure_contact.structure.libelle, structure_contact.structure.libelle
    )
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(f"{agent_contact.agent.nom} {agent_contact.agent.prenom}").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()

    expect(page.locator("[data-testid='contacts-agents']").get_by_text(str(agent_contact), exact=True)).to_be_visible()
    expect(
        page.locator("[data-testid='contacts-structures']").get_by_text(str(structure_contact), exact=True)
    ).to_be_visible()


def test_add_multiple_agent_contacts_adds_structure_contact_once(live_server, page, choice_js_fill):
    """Test que l'ajout de plusieurs contacts agents de la même structure n'ajoute qu'une seule fois le contact structure"""
    structure_contact = ContactStructureFactory()
    contact_agent_1, contact_agent_2 = ContactAgentFactory.create_batch(2, agent__structure=structure_contact.structure)
    for contact_agent in (contact_agent_1, contact_agent_2):
        contact_agent.agent.user.is_active = True
        contact_agent.agent.user.save()
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}/{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", str(structure_contact.structure), str(structure_contact.structure))
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(f"{contact_agent_1.agent.nom} {contact_agent_1.agent.prenom}").click()
    page.get_by_text(f"{contact_agent_2.agent.nom} {contact_agent_2.agent.prenom}").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()
    page.get_by_role("tab", name="Contacts").click()

    agents_section = page.locator("[data-testid='contacts-agents']")
    expect(agents_section.get_by_text(str(contact_agent_1.agent), exact=True)).to_be_visible()
    expect(agents_section.get_by_text(str(contact_agent_2.agent), exact=True)).to_be_visible()

    structures_section = page.locator("[data-testid='contacts-structures']")
    expect(structures_section).to_have_count(1)
    expect(structures_section.get_by_text(str(structure_contact.structure), exact=True)).to_be_visible()
