from datetime import datetime

from django.utils import timezone
from playwright.sync_api import Page, expect

from core.factories import StructureFactory
from sa.models.evenement import StatutEvenement
from sa.tests.factories import EspeceFactory, EvenementAnimalFactory, MaladieFactory, TuberculoseFactory
from sa.tests.pages import EvenementListPage


def test_search_form_have_all_fields(live_server, page: Page):
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    expect(page.get_by_role("heading", name="Rechercher un événement")).to_be_visible()
    expect(search_page.annee_field).to_be_visible()
    expect(search_page.maladie_treeselect.main_button).to_be_visible()
    expect(search_page.numero_field).to_be_visible()
    expect(search_page.espece_treeselect.main_button).to_be_visible()
    expect(search_page.statut_field).to_be_visible()
    expect(search_page.statut_field).to_have_value("")
    expect(search_page.statut_field.locator("option:checked")).to_have_text("Tous")
    expect(search_page.start_date_field).to_be_visible()
    expect(search_page.end_date_field).to_be_visible()
    expect(search_page.full_text_search_field).to_be_visible()
    expect(search_page.full_text_search_field).to_have_attribute("placeholder", "Tous champs")
    expect(search_page.departement_treeselect.main_button).to_be_visible()
    expect(search_page.numero_adis_field).to_be_visible()
    expect(search_page.commune_field).to_be_visible()
    expect(search_page.etat_field).to_be_visible()
    expect(page.get_by_role("button", name="Effacer", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="Rechercher")).to_be_visible()


def test_reset_button_clears_form_and_search(live_server, page: Page):
    maladie = MaladieFactory()
    matching = EvenementAnimalFactory(maladie=maladie, commune="Challans")
    other = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.annee_field.fill(str(matching.numero_annee))
    search_page.select_maladie(maladie)
    search_page.commune_field.fill("Challans")
    search_page.submit_search()
    expect(search_page.row(other.numero)).to_have_count(0)

    search_page.reset_search()

    expect(search_page.annee_field).to_be_empty()
    expect(search_page.commune_field).to_be_empty()
    expect(search_page.maladie_treeselect.selected_tags).to_have_count(0)
    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_be_visible()


def test_evenement_animal_list_displays_events_and_links_to_details(live_server, page: Page):
    evenement = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    row = search_page.row(evenement.numero)
    expect(row).to_be_visible()
    expect(row).to_contain_text(evenement.maladie.name)
    expect(row).to_contain_text(evenement.espece.name)
    expect(row).to_contain_text(evenement.get_statut_evenement_display())
    expect(row).to_contain_text(evenement.get_etat_display())

    row.get_by_role("link", name=evenement.numero, exact=True).click()
    page.wait_for_url(f"**{evenement.get_absolute_url()}")


def test_evenement_animal_list_compteur(live_server, page: Page):
    EvenementAnimalFactory.create_batch(3)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    expect(page.get_by_text("3 sur un total de 3")).to_be_visible()


def test_evenement_animal_list_filter_by_annee(live_server, page: Page):
    matching = EvenementAnimalFactory(numero_annee=2025)
    other = EvenementAnimalFactory(numero_annee=2026)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.annee_field.fill("2025")
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_maladie(live_server, page: Page):
    maladie = MaladieFactory()
    matching = EvenementAnimalFactory(maladie=maladie)
    other = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.select_maladie(maladie)
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)
    expect(search_page.maladie_treeselect.main_button).to_have_text(maladie.name_with_acronym)


def test_evenement_animal_list_filter_by_espece_courante(live_server, page: Page):
    espece = EspeceFactory(is_highlighted=True)
    matching = EvenementAnimalFactory(espece=espece)
    other = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.select_espece(espece)
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_autre_espece(live_server, page: Page):
    espece = EspeceFactory(is_highlighted=False)
    matching = EvenementAnimalFactory(espece=espece)
    other = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.select_espece(espece)
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)
    expect(search_page.espece_treeselect.main_button).to_have_text(espece.name)


def test_evenement_animal_list_filter_by_numero(live_server, page: Page):
    maladie = TuberculoseFactory()
    evenement_12 = EvenementAnimalFactory(maladie=maladie, numero_annee=2026, numero_evenement=12)
    evenement_112 = EvenementAnimalFactory(maladie=maladie, numero_annee=2026, numero_evenement=112)
    evenement_3 = EvenementAnimalFactory(maladie=maladie, numero_annee=2026, numero_evenement=3)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.numero_field.fill("12")
    search_page.submit_search()

    expect(search_page.row(evenement_12.numero)).to_be_visible()
    expect(search_page.row(evenement_112.numero)).to_be_visible()
    expect(search_page.row(evenement_3.numero)).to_have_count(0)

    search_page.numero_field.fill(f"{maladie.acronym.lower()}-2026.11")
    search_page.submit_search()

    expect(search_page.row(evenement_112.numero)).to_be_visible()
    expect(search_page.row(evenement_12.numero)).to_have_count(0)
    expect(search_page.row(evenement_3.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_statut(live_server, page: Page):
    matching = EvenementAnimalFactory(statut_evenement=StatutEvenement.CONFIRME)
    other = EvenementAnimalFactory(statut_evenement=StatutEvenement.SUSPECT)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    expect(search_page.statut_field.locator("option")).to_have_text(
        ["Tous", "Confirmé", "Infirmé", "Non retenu", "Suspect"]
    )
    search_page.statut_field.select_option(label="Confirmé")
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_date_publication(live_server, page: Page):
    matching = EvenementAnimalFactory(date_publication=timezone.make_aware(datetime(2026, 3, 15, 10)))
    too_late = EvenementAnimalFactory(date_publication=timezone.make_aware(datetime(2026, 6, 1, 10)))
    not_published = EvenementAnimalFactory(date_publication=None)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.start_date_field.fill("2026-03-01")
    search_page.end_date_field.fill("2026-03-31")
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(too_late.numero)).to_have_count(0)
    expect(search_page.row(not_published.numero)).to_have_count(0)


def test_evenement_animal_list_full_text_search(live_server, page: Page):
    by_raison_sociale = EvenementAnimalFactory(raison_sociale_etablissement="GAEC des Prés Fleuris")
    by_description = EvenementAnimalFactory(description="Mortalité observée près des prés fleuris")
    by_commentaire = EvenementAnimalFactory(commentaire="Animaux déplacés vers les Prés fleuris")
    other = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.full_text_search_field.fill("pres fleuris")
    search_page.submit_search()

    expect(search_page.row(by_raison_sociale.numero)).to_be_visible()
    expect(search_page.row(by_description.numero)).to_be_visible()
    expect(search_page.row(by_commentaire.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_departement(live_server, page: Page, ensure_departements):
    ille_et_vilaine, *_ = ensure_departements("Ille-et-Vilaine", "Finistère", "Vendée")
    in_ille_et_vilaine = EvenementAnimalFactory(code_insee="35238")
    in_finistere = EvenementAnimalFactory(code_insee="29019")
    in_vendee = EvenementAnimalFactory(code_insee="85047")

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.select_departement(ille_et_vilaine)
    search_page.submit_search()

    expect(search_page.row(in_ille_et_vilaine.numero)).to_be_visible()
    expect(search_page.row(in_finistere.numero)).to_have_count(0)
    expect(search_page.row(in_vendee.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_departement_in_corse(live_server, page: Page, ensure_departements):
    corse_du_sud, *_ = ensure_departements("Corse-du-Sud", "Haute-Corse")
    in_corse_du_sud = EvenementAnimalFactory(code_insee="2A004")
    in_haute_corse = EvenementAnimalFactory(code_insee="2B033")

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.select_departement(corse_du_sud)
    search_page.submit_search()

    expect(search_page.row(in_corse_du_sud.numero)).to_be_visible()
    expect(search_page.row(in_haute_corse.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_region(live_server, page: Page, ensure_departements):
    ille_et_vilaine, *_ = ensure_departements("Ille-et-Vilaine", "Finistère", "Vendée")
    in_ille_et_vilaine = EvenementAnimalFactory(code_insee="35238")
    in_finistere = EvenementAnimalFactory(code_insee="29019")
    in_vendee = EvenementAnimalFactory(code_insee="85047")

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.select_region(ille_et_vilaine.region)
    search_page.submit_search()

    expect(search_page.row(in_ille_et_vilaine.numero)).to_be_visible()
    expect(search_page.row(in_finistere.numero)).to_be_visible()
    expect(search_page.row(in_vendee.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_numero_adis(live_server, page: Page):
    matching = EvenementAnimalFactory(numero_adis="FR-2026-98765")
    other = EvenementAnimalFactory(numero_adis="FR-2026-12345")

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.numero_adis_field.fill("98765")
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_commune_du_foyer(live_server, page: Page):
    matching = EvenementAnimalFactory(commune="Challans", code_insee="85047")
    detenteur_only = EvenementAnimalFactory(
        commune="Nantes", code_insee="44109", commune_etablissement="Challans", code_insee_etablissement="85047"
    )

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.commune_field.fill("challans")
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(detenteur_only.numero)).to_have_count(0)

    search_page.commune_field.fill("85047")
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(detenteur_only.numero)).to_have_count(0)


def test_evenement_animal_list_combines_filters(live_server, page: Page):
    maladie = MaladieFactory()
    matching = EvenementAnimalFactory(maladie=maladie, statut_evenement=StatutEvenement.CONFIRME)
    same_maladie = EvenementAnimalFactory(maladie=maladie, statut_evenement=StatutEvenement.SUSPECT)
    same_statut = EvenementAnimalFactory(statut_evenement=StatutEvenement.CONFIRME)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.select_maladie(maladie)
    search_page.statut_field.select_option(label="Confirmé")
    search_page.submit_search()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(same_maladie.numero)).to_have_count(0)
    expect(search_page.row(same_statut.numero)).to_have_count(0)


def test_evenement_animal_list_cant_see_draft_of_other_structure(live_server, page: Page):
    evenement = EvenementAnimalFactory()
    evenement.createur = StructureFactory()
    evenement.save()
    assert evenement.is_draft is True

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    expect(page.get_by_text("0 sur un total de 0")).to_be_visible()
