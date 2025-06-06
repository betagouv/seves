import pytest
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE
from core.factories import StructureFactory
from core.models import LienLibre, Structure, Visibilite
from ..factories import EvenementFactory, OrganismeNuisibleFactory
from ..factories import StatutReglementaireFactory
from ..models import StatutReglementaire, Evenement


def test_update_evenement(live_server, page: Page, choice_js_fill):
    nuisible = OrganismeNuisibleFactory()
    statut, _ = StatutReglementaire.objects.get_or_create(libelle="organisme quarantaine prioritaire")
    evenement = EvenementFactory(organisme_nuisible__libelle_court="FOO", statut_reglementaire=statut)
    page.goto(f"{live_server.url}{evenement.get_update_url()}")
    expect(page.get_by_role("heading", name=f"Événement n°{evenement.numero}")).to_be_visible()
    expect(page.get_by_label("Statut réglementaire")).to_have_value(str(statut.pk))
    expect(page.get_by_label("Organisme nuisible")).to_have_value(str(evenement.organisme_nuisible.pk))

    choice_js_fill(page, ".choices__list--single", nuisible.libelle_court, nuisible.libelle_court)
    page.get_by_label("Statut réglementaire").select_option("organisme émergent")
    page.get_by_role("button", name="Enregistrer").click()

    evenement.refresh_from_db()
    assert evenement.organisme_nuisible.libelle_court == nuisible.libelle_court
    assert evenement.statut_reglementaire.libelle == "organisme émergent"

    expect(page.get_by_text(nuisible.libelle_court)).to_be_visible()
    expect(page.get_by_text("organisme émergent")).to_be_visible()


def test_update_evenement_can_add_and_delete_free_links(
    live_server,
    page: Page,
    choice_js_fill,
):
    evenement = EvenementFactory()
    evenement_to_delete = EvenementFactory()
    evenement_to_add = EvenementFactory()
    LienLibre.objects.create(related_object_1=evenement, related_object_2=evenement_to_delete)

    page.goto(f"{live_server.url}{evenement.get_update_url()}")

    expect(page.get_by_text(f"Événement : {str(evenement_to_delete.numero)}Remove")).to_be_visible()
    page.get_by_text(f"Événement : {str(evenement_to_delete.numero)}Remove").click()

    page.locator(".choices__button").click()
    evenement_input = "Événement : " + str(evenement_to_add.numero)
    choice_js_fill(page, "#liens-libre .choices", str(evenement_to_add.numero), evenement_input)

    page.get_by_role("button", name="Enregistrer").click()

    lien_libre = LienLibre.objects.get()
    assert lien_libre.related_object_1 == evenement
    assert lien_libre.related_object_2 == evenement_to_add

    expect(page.get_by_role("link", name=str(evenement_to_add.numero))).to_be_visible()
    expect(page.get_by_role("link", name=str(evenement_to_add.numero))).to_have_attribute("target", "_blank")
    expect(page.get_by_role("link", name=str(evenement_to_delete.numero))).not_to_be_visible()


def test_update_evenement_cant_add_self_links(
    live_server,
    page: Page,
    choice_js_cant_pick,
):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_update_url()}")

    fiche_input = "Événement : " + str(evenement.numero)
    choice_js_cant_pick(page, "#liens-libre .choices", str(evenement.numero), fiche_input)


def test_cant_access_update_form_evenement_if_no_rights(live_server, page: Page, choice_js_fill):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    evenement.createur = Structure.objects.create(niveau1="Other structure")
    evenement.save()

    response = page.goto(f"{live_server.url}{evenement.get_update_url()}")
    assert response.status == 403


@pytest.mark.django_db
def test_cant_update_evenement_i_cant_see(client):
    organisme_nuisible = OrganismeNuisibleFactory()
    evenement = EvenementFactory(createur=StructureFactory())
    response = client.get(evenement.get_update_url())
    assert response.status_code == 403

    response = client.post(evenement.get_update_url(), data={"organisme_nuisible": organisme_nuisible.pk})

    assert response.status_code == 403
    evenement.refresh_from_db()
    assert evenement.organisme_nuisible != organisme_nuisible


def test_update_evenement_adds_agent_and_structure_contacts(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    """Test que la modification d'un événement ajoute l'agent et sa structure comme contacts"""
    evenement = EvenementFactory()
    statut = StatutReglementaireFactory()

    # Modification de l'événement
    page.goto(f"{live_server.url}{evenement.get_update_url()}")
    page.get_by_label("Statut réglementaire").select_option(str(statut.pk))
    page.get_by_role("button", name="Enregistrer").click()

    # Vérification des contacts
    evenement.refresh_from_db()
    assert evenement.contacts.filter(agent=mocked_authentification_user.agent).exists()
    assert evenement.contacts.filter(structure=mocked_authentification_user.agent.structure).exists()

    # Vérification de l'interface
    page.get_by_test_id("contacts").click()
    expect(
        page.locator("[data-testid='contacts-agents']").get_by_text(str(mocked_authentification_user.agent), exact=True)
    ).to_be_visible()
    expect(
        page.locator("[data-testid='contacts-structures']").get_by_text(
            str(mocked_authentification_user.agent.structure), exact=True
        )
    ).to_be_visible()


def test_update_evenement_multiple_times_adds_contacts_once(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    """Test que plusieurs modifications d'un événement n'ajoutent qu'une fois les contacts"""
    evenement = EvenementFactory()
    statut1, statut2 = StatutReglementaireFactory.create_batch(2)

    # Première modification
    page.goto(f"{live_server.url}{evenement.get_update_url()}")
    page.get_by_label("Statut réglementaire").select_option(str(statut1.pk))
    page.get_by_role("button", name="Enregistrer").click()

    # Seconde modification
    page.goto(f"{live_server.url}{evenement.get_update_url()}")
    page.get_by_label("Statut réglementaire").select_option(str(statut2.pk))
    page.get_by_role("button", name="Enregistrer").click()

    # Vérification des contacts
    evenement.refresh_from_db()
    assert evenement.contacts.filter(agent=mocked_authentification_user.agent).count() == 1
    assert evenement.contacts.filter(structure=mocked_authentification_user.agent.structure).count() == 1

    # Vérification de l'interface
    page.get_by_test_id("contacts").click()
    expect(
        page.locator("[data-testid='contacts-agents']").get_by_text(str(mocked_authentification_user.agent), exact=True)
    ).to_be_visible()
    expect(
        page.locator("[data-testid='contacts-structures']").get_by_text(
            str(mocked_authentification_user.agent.structure), exact=True
        )
    ).to_be_visible()


def test_update_evenement_cant_select_draft_evenement_in_free_links(
    live_server,
    page: Page,
    choice_js_cant_pick,
):
    evenement = EvenementFactory()
    draft_evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    page.goto(f"{live_server.url}{evenement.get_update_url()}")

    fiche_input = "Événement : " + str(draft_evenement.numero)
    choice_js_cant_pick(page, "#liens-libre .choices", str(draft_evenement.numero), fiche_input)


def test_update_evenement_free_links_filtered_by_user_visibility(
    live_server,
    page: Page,
    mocked_authentification_user,
):
    # Événement visible en national
    visible_evenement = EvenementFactory(visibilite=Visibilite.NATIONALE)

    # Événement en visibilité limitée avec structure autorisée
    limited_visible_evenement = EvenementFactory()
    limited_visible_evenement.visibilite = Visibilite.LIMITEE
    limited_visible_evenement.allowed_structures.add(mocked_authentification_user.agent.structure)
    limited_visible_evenement.save()

    # Événement en visibilité limitée sans accès
    hidden_evenement = EvenementFactory(createur=Structure.objects.create(niveau1="test"))

    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_update_url()}")
    page.locator("#liens-libre .choices").click()

    expect(page.get_by_role("option", name=str(visible_evenement.numero))).to_be_visible()
    expect(page.get_by_role("option", name=str(limited_visible_evenement.numero))).to_be_visible()
    expect(page.get_by_role("option", name=str(hidden_evenement.numero))).not_to_be_visible()


def test_update_evenement_has_locking_protection(live_server, page: Page, choice_js_fill):
    nuisible = OrganismeNuisibleFactory()
    statut, _ = StatutReglementaire.objects.get_or_create(libelle="organisme quarantaine prioritaire")
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_update_url()}")

    evenement.organisme_nuisible = OrganismeNuisibleFactory()
    evenement.save()

    choice_js_fill(page, ".choices__list--single", nuisible.libelle_court, nuisible.libelle_court)
    page.get_by_label("Statut réglementaire").select_option("organisme émergent")
    page.get_by_role("button", name="Enregistrer").click()

    evenement.refresh_from_db()
    assert evenement.organisme_nuisible.libelle_court != nuisible.libelle_court

    initial_timestamp = page.evaluate("performance.timing.navigationStart")
    expect(
        page.get_by_text(
            "Vos modifications n'ont pas été enregistrées. Un autre utilisateur a modifié cet objet. Fermer cette modale pour charger la dernière version."
        )
    ).to_be_visible()
    page.keyboard.press("Escape")
    page.wait_for_function(f"performance.timing.navigationStart > {initial_timestamp}")


def test_update_evenement_as_ac_can_access_rasff_europhyt(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementFactory()
    structure = mocked_authentification_user.agent.structure
    structure.niveau1 = AC_STRUCTURE
    structure.save()

    page.goto(f"{live_server.url}{evenement.get_update_url()}")
    page.get_by_label("Numéro Europhyt").fill("1" * 8)
    page.get_by_label("Numéro Rasff").fill("2" * 9)
    page.get_by_role("button", name="Enregistrer").click()
    page.wait_for_timeout(600)

    evenement.refresh_from_db()
    assert evenement.numero_europhyt == "1" * 8
    assert evenement.numero_rasff == "2" * 9


@pytest.mark.django_db
def test_fiche_detection_update_cant_forge_form_to_edit_rasff_europhyt(
    live_server, page: Page, mocked_authentification_user
):
    evenement = EvenementFactory(numero_europhyt="", numero_rasff="")
    page.goto(f"{live_server.url}{evenement.get_update_url()}")
    page.evaluate("""
            const form = document.querySelector('main form');
            const input1 = document.createElement('input');
            input1.name = 'numero_europhyt';
            input1.value = '11111111';
            form.appendChild(input1);

            const input2 = document.createElement('input');
            input2.name = 'numero_rasff';
            input2.placeholder = '222222222';
            form.appendChild(input2);
        """)

    page.get_by_role("button", name="Enregistrer").click()
    page.wait_for_timeout(600)
    evenement.refresh_from_db()
    assert evenement.numero_europhyt == ""
    assert evenement.numero_rasff == ""


def test_edit_button_not_visible_if_evenement_cloture(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("button", name="Actions")).not_to_be_visible()
    expect(page.get_by_role("link", name="Modifier l'événement")).not_to_be_visible()


def test_cant_access_update_page_if_evenement_cloture(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    page.goto(f"{live_server.url}{evenement.get_update_url()}")
    expect(page.get_by_text("Vous n'avez pas le droit d'accéder à cette page.")).to_be_visible()
