import pytest
from django.contrib.contenttypes.models import ContentType
from django.utils.http import urlencode
from playwright.sync_api import expect
from model_bakery import baker
from django.urls import reverse

from core.models import Contact, Structure, Agent, Visibilite
from sv.models import FicheDetection


@pytest.fixture
def contact(db):
    structure = baker.make(Structure, _fill_optional=True)
    agent = baker.make(Agent, structure=structure)
    user = agent.user
    user.is_active = True
    user.save()
    return baker.make(Contact, agent=agent)


@pytest.fixture
def contacts(db):
    # creation de deux contacts de type Agent
    agent1, agent2 = baker.make(Agent, _quantity=2)
    baker.make(Contact, agent=agent1)
    baker.make(Contact, agent=agent2)
    # création de la structure MUS et de deux contacts de type Agent associés
    structure_mus = baker.make(Structure, libelle="MUS")
    agentMUS1, agentMUS2 = baker.make(Agent, _quantity=2, structure=structure_mus)
    for agent in (agentMUS1, agentMUS2):
        user = agent.user
        user.is_active = True
        user.save()
    contactMUS1 = baker.make(Contact, agent=agentMUS1)
    contactMUS2 = baker.make(Contact, agent=agentMUS2)
    return [contactMUS1, contactMUS2]


def test_add_contact_form(live_server, page, fiche_variable, mocked_authentification_user):
    """Test l'affichage du formulaire d'ajout de contact"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()

    expect(page.get_by_role("link", name="Retour à la fiche")).to_be_visible()
    expect(page.get_by_role("heading", name="Ajouter un agent")).to_be_visible()
    expect(page.get_by_text("Structure", exact=True)).to_be_visible()
    expect(page.get_by_text(mocked_authentification_user.agent.structure.libelle).nth(1)).to_be_visible()
    expect(page.get_by_role("button", name="Rechercher")).to_be_visible()


def test_cant_access_add_contact_form_if_fiche_brouillon(live_server, page, fiche_variable):
    fiche = fiche_variable()
    fiche.visibilite = Visibilite.BROUILLON
    fiche.numero = None
    fiche.save()
    content_type = ContentType.objects.get_for_model(fiche)
    page.goto(
        f"{live_server.url}/{reverse('contact-add-form')}?fiche_id={fiche.id}&content_type_id={content_type.id}&next={fiche.get_absolute_url()}"
    )
    expect(page.get_by_text("Action impossible car la fiche est en brouillon")).to_be_visible()


def test_add_contact_form_back_to_fiche(live_server, page, fiche_variable):
    """Test le lien de retour vers la fiche"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche.get_absolute_url()}")


@pytest.mark.django_db
def test_structure_list(live_server, page):
    """Test que la liste des structures soit bien dans le contexte du formulaire d'ajout de contact"""
    Contact.objects.all().delete()
    Agent.objects.all().delete()
    Structure.objects.all().delete()
    for i in range(0, 3):
        structure = baker.make(Structure, libelle=f"Structure {i+1}")
        agent = baker.make(Agent, structure=structure)
        user = agent.user
        user.is_active = True
        user.save()
        baker.make(Contact, email="foo@example.com", agent=agent)
    assert Structure.objects.count() == 3

    fiche = FicheDetection.objects.create(visibilite=Visibilite.LOCAL, createur=Structure.objects.first())
    url = f"{reverse('contact-add-form')}?{urlencode({'fiche_id': fiche.pk, 'content_type_id': ContentType.objects.get_for_model(fiche).id, 'next': fiche.get_absolute_url()})}"
    page.goto(f"{live_server.url}{url}")

    page.query_selector(".choices").click()
    page.wait_for_selector("input:focus", state="visible", timeout=2_000)
    page.locator("*:focus").fill("Structure")
    for i in range(0, 3):
        expect(page.get_by_role("option", name=f"Structure {i+1}", exact=True)).to_be_visible()


def test_add_contact_form_select_structure(live_server, page, fiche_variable, contacts, choice_js_fill):
    """Test l'affichage des contacts dans le formulaire de sélection suite à la selection d'une structure"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
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


def test_cant_add_contact_form_select_structure_if_fiche_brouillon(client, fiche_variable):
    """Test que si une fiche est en visibilité brouillon, on ne peut pas afficher des contacts dans le formulaire de sélection suite à la selection d'une structure"""
    fiche = fiche_variable()
    fiche.visibilite = Visibilite.BROUILLON
    fiche.numero = None
    fiche.save()

    response = client.post(
        reverse("contact-add-form"),
        data={
            "fiche_id": fiche.id,
            "structure": fiche.createur,
            "next": fiche.get_absolute_url(),
            "content_type_id": ContentType.objects.get_for_model(fiche).id,
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_add_contact_to_a_fiche(live_server, page, fiche_variable, contacts, choice_js_fill):
    """Test l'ajout d'un contact à une fiche de détection"""
    fiche = fiche_variable()
    contact1 = contacts[0]
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", "MUS", "MUS")
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_text(f"{contact1.agent.nom} {contact1.agent.prenom}").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()
    page.get_by_role("tab", name="Contacts").click()

    expect(page.get_by_text("Le contact a été ajouté avec succès.")).to_be_visible()
    expect(page.locator(".fr-card__content")).to_be_visible()


def test_cant_add_inactive_contact_to_a_fiche(live_server, page, fiche_variable, contacts, choice_js_fill):
    contact1 = contacts[0]
    user = contact1.agent.user
    user.is_active = False
    user.save()

    page.goto(f"{live_server.url}/{fiche_variable().get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", "MUS", "MUS")
    page.get_by_role("button", name="Rechercher").click()
    expect(page.get_by_text(f"{contact1.agent.nom} {contact1.agent.prenom}")).not_to_be_visible()
    expect(page.get_by_text(f"{contacts[1].agent.nom} {contacts[1].agent.prenom}")).to_be_visible()


def test_add_multiple_contacts_to_a_fiche(live_server, page, fiche_variable, contacts, choice_js_fill):
    """Test l'ajout de plusieurs contacts à une fiche de détection"""
    fiche = fiche_variable()
    contact1 = contacts[0]
    contact2 = contacts[1]
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
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


def test_no_contact_selected(live_server, page, fiche_variable, contact, choice_js_fill):
    """Test l'affichage d'un message d'erreur si aucun contact n'est sélectionné"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", contact.agent.structure.libelle, contact.agent.structure.libelle)
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()

    expect(page.get_by_text("Veuillez sélectionner au")).to_be_visible()
    expect(page.locator("#form-selection")).to_contain_text("Veuillez sélectionner au moins un contact")


def test_add_contact_form_back_to_fiche_after_select_structure(
    live_server, page, fiche_variable, contact, choice_js_fill
):
    """Test le lien de retour vers la fiche après la selection d'une structure et l'affichage des contacts associés"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", contact.agent.structure.libelle, contact.agent.structure.libelle)
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche.get_absolute_url()}")


def test_add_contact_form_back_to_fiche_after_error_message(live_server, page, fiche_variable, contact, choice_js_fill):
    """Test le lien de retour vers la fiche après l'affichage du message d'erreur si aucun contact n'est sélectionné"""
    fiche = fiche_variable()
    page.goto(f"{live_server.url}/{fiche.get_absolute_url()}")
    page.get_by_role("tab", name="Contacts").click()
    page.get_by_role("link", name="Ajouter un agent").click()
    choice_js_fill(page, ".choices__list--single", contact.agent.structure.libelle, contact.agent.structure.libelle)
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter les contacts sélectionnés").click()
    page.get_by_role("link", name="Retour à la fiche").click()

    expect(page).to_have_url(f"{live_server.url}{fiche.get_absolute_url()}")


def test_cant_add_contact_if_fiche_brouillon(client, fiche_variable, contact):
    fiche = fiche_variable()
    fiche.visibilite = Visibilite.BROUILLON
    fiche.numero = None
    fiche.save()

    response = client.post(
        reverse("contact-add-form-select-agents"),
        data={
            "structure": contact.agent.structure.id,
            "contacts": [contact.id],
            "content_type_id": ContentType.objects.get_for_model(fiche).id,
            "fiche_id": fiche.id,
            "next": fiche.get_absolute_url(),
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_cant_delete_contact_if_fiche_brouillon(client, fiche_variable, contact):
    fiche = fiche_variable()
    fiche.visibilite = Visibilite.BROUILLON
    fiche.numero = None
    fiche.save()
    fiche.contacts.set([contact])

    response = client.post(
        reverse("contact-delete"),
        data={
            "content_type_pk": ContentType.objects.get_for_model(fiche).id,
            "fiche_pk": fiche.id,
            "pk": contact.id,
            "next": fiche.get_absolute_url(),
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"
