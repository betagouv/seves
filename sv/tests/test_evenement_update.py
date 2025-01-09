from playwright.sync_api import Page, expect

from core.models import LienLibre, Visibilite, Structure
from ..factories import EvenementFactory, OrganismeNuisibleFactory
from ..models import StatutReglementaire


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


def test_cant_access_update_evenement_if_no_rights(live_server, page: Page, choice_js_fill):
    evenement = EvenementFactory(visibilite=Visibilite.BROUILLON)
    evenement.createur = Structure.objects.create(niveau1="Other structure")
    evenement.save()

    response = page.goto(f"{live_server.url}{evenement.get_update_url()}")
    assert response.status == 403
