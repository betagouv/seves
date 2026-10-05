from datetime import date, datetime

from django.utils import timezone
from playwright.sync_api import Page, expect
import pytest

from core.factories import StructureFactory
from core.mixins import WithEtatMixin
from sa.models.analyse import ResultatAnalyse
from sa.models.evenement import ContexteSuspicion, StatutAnimal, StatutEvenement, TypeLieu
from sa.tests.factories import (
    AnalyseFactory,
    EspeceFactory,
    EvenementAnimalFactory,
    MaladieFactory,
    TuberculoseFactory,
    VeterinaireFactory,
)
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
    expect(search_page.advanced_filters_button).to_be_visible()
    expect(search_page.advanced_filters).to_be_hidden()
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
    expect(row).to_contain_text(evenement.departement.numero)
    expect(row).to_contain_text(f"{evenement.commune} ({evenement.code_insee})")
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


def test_evenement_animal_list_filter_by_etat(live_server, page: Page):
    en_cours = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    cloture = EvenementAnimalFactory(etat=WithEtatMixin.Etat.CLOTURE)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"État": "Clôturé"})

    expect(search_page.row(cloture.numero)).to_be_visible()
    expect(search_page.row(en_cours.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_date_confirmation(live_server, page: Page):
    matching = EvenementAnimalFactory(statut_evenement=StatutEvenement.CONFIRME, date_statut_changed=date(2026, 3, 15))
    too_late = EvenementAnimalFactory(statut_evenement=StatutEvenement.CONFIRME, date_statut_changed=date(2026, 4, 1))
    not_confirmed = EvenementAnimalFactory(
        statut_evenement=StatutEvenement.SUSPECT, date_statut_changed=date(2026, 3, 15)
    )

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_advanced_filters()
    search_page.fill_advanced_date_range("Date de confirmation entre le", "2026-03-01", "2026-03-31")
    search_page.apply_advanced_filters()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(too_late.numero)).to_have_count(0)
    expect(search_page.row(not_confirmed.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_resultat_confirmation(live_server, page: Page):
    matching = AnalyseFactory(resultat=ResultatAnalyse.DETECTE_FAIBLE).evenement
    other = AnalyseFactory(resultat=ResultatAnalyse.NON_DETECTE).evenement
    without_analyse = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"Résultat de confirmation": "Détecté faible"})

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)
    expect(search_page.row(without_analyse.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_contexte_suspicion(live_server, page: Page):
    matching = EvenementAnimalFactory(context_suspicion=ContexteSuspicion.CLINIQUE)
    other = EvenementAnimalFactory(context_suspicion=ContexteSuspicion.ANALYTIQUE)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"Contexte de la suspicion": "Clinique"})

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


@pytest.mark.parametrize(
    "label,model_field",
    [
        ("Date des premiers symptômes entre le", "date_first_symptoms"),
        ("Date APDI entre le", "date_apdi"),
        ("Date APMS entre le", "date_apms"),
        ("Date de levée APDI / APMS entre le", "date_levee"),
    ],
)
def test_evenement_animal_list_filter_by_date_range(live_server, page: Page, label, model_field):
    matching = EvenementAnimalFactory(**{model_field: date(2026, 3, 15)})
    too_early = EvenementAnimalFactory(**{model_field: date(2026, 2, 28)})
    too_late = EvenementAnimalFactory(**{model_field: date(2026, 4, 1)})
    without_date = EvenementAnimalFactory(**{model_field: None})

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_advanced_filters()
    search_page.fill_advanced_date_range(label, "2026-03-01", "2026-03-31")
    search_page.apply_advanced_filters()

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(too_early.numero)).to_have_count(0)
    expect(search_page.row(too_late.numero)).to_have_count(0)
    expect(search_page.row(without_date.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_type_detenteur(live_server, page: Page):
    etablissement = EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU)
    particulier = EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU, particulier=True)
    sauvage = EvenementAnimalFactory(statut_animal=StatutAnimal.SAUVAGE)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_advanced_filters()
    search_page.advanced_filters.get_by_text("Établissement", exact=True).click()
    search_page.apply_advanced_filters()

    expect(search_page.row(etablissement.numero)).to_be_visible()
    expect(search_page.row(particulier.numero)).to_have_count(0)
    expect(search_page.row(sauvage.numero)).to_have_count(0)

    search_page.open_advanced_filters()
    search_page.advanced_filters.get_by_text("Particulier", exact=True).click()
    search_page.apply_advanced_filters()

    expect(search_page.row(particulier.numero)).to_be_visible()
    expect(search_page.row(etablissement.numero)).to_have_count(0)
    expect(search_page.row(sauvage.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_numero_identifiant_detenteur(live_server, page: Page):
    by_identifiant = EvenementAnimalFactory(numero_identifiant_etablissement="FR85123456")
    by_siret = EvenementAnimalFactory(siret_etablissement="12345678901234")
    other = EvenementAnimalFactory(numero_identifiant_etablissement="FR44000000", siret_etablissement="98765432109876")

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"N° identifiant": "85123"})

    expect(search_page.row(by_identifiant.numero)).to_be_visible()
    expect(search_page.row(by_siret.numero)).to_have_count(0)
    expect(search_page.row(other.numero)).to_have_count(0)

    search_page.search_with_advanced_filters({"N° identifiant": "456789012"})

    expect(search_page.row(by_siret.numero)).to_be_visible()
    expect(search_page.row(by_identifiant.numero)).to_have_count(0)
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_commune_detenteur(live_server, page: Page):
    etablissement = EvenementAnimalFactory(
        statut_animal=StatutAnimal.DETENU, commune_etablissement="Les Sables-d'Olonne"
    )
    particulier = EvenementAnimalFactory(
        statut_animal=StatutAnimal.DETENU, particulier=True, commune_particulier="Olonne-sur-Mer"
    )
    foyer_only = EvenementAnimalFactory(commune="Olonne-sur-Mer", commune_etablissement="Nantes")

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"Commune": "olonne"})

    expect(search_page.row(etablissement.numero)).to_be_visible()
    expect(search_page.row(particulier.numero)).to_be_visible()
    expect(search_page.row(foyer_only.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_nom_detenteur(live_server, page: Page):
    etablissement = EvenementAnimalFactory(
        statut_animal=StatutAnimal.DETENU, raison_sociale_etablissement="GAEC Bérard"
    )
    particulier = EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU, particulier=True, nom_particulier="Bérardi")
    other = EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU, raison_sociale_etablissement="EARL Martin")

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"Nom / raison sociale": "berard"})

    expect(search_page.row(etablissement.numero)).to_be_visible()
    expect(search_page.row(particulier.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_type_lieu(live_server, page: Page):
    matching = EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU, type_lieu=TypeLieu.ZOO)
    other = EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU, type_lieu=TypeLieu.SLAUGHTERHOUSE)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"Type de lieu": "Parc zoologique"})

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_veterinaire(live_server, page: Page):
    by_structure = VeterinaireFactory(nom_structure="Clinique vétérinaire du Bocage", nom="Durand").evenement
    by_nom = VeterinaireFactory(nom_structure="Cabinet Vendée", nom="Bocagé").evenement
    other = VeterinaireFactory(nom_structure="Clinique des Lacs", nom="Martin").evenement
    without_veterinaire = EvenementAnimalFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"Structure ou vétérinaire": "bocage"})

    expect(search_page.row(by_structure.numero)).to_be_visible()
    expect(search_page.row(by_nom.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)
    expect(search_page.row(without_veterinaire.numero)).to_have_count(0)


def test_evenement_animal_list_filter_by_numero_dpe(live_server, page: Page):
    matching = VeterinaireFactory(numero_dpe="DPE-123456").evenement
    other = VeterinaireFactory(numero_dpe="DPE-999999").evenement

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"N° DPE": "3456"})

    expect(search_page.row(matching.numero)).to_be_visible()
    expect(search_page.row(other.numero)).to_have_count(0)


def test_evenement_animal_list_advanced_filters_counter(live_server, page: Page):
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    expect(search_page.advanced_filters_button).to_have_text("Filtres avancés")

    search_page.open_advanced_filters()
    search_page.advanced_filters.get_by_text("Particulier", exact=True).click()
    search_page.advanced_field("N° DPE").fill("123")
    search_page.apply_advanced_filters()

    expect(search_page.advanced_filters_button).to_have_text("Filtres avancés 2")


def test_evenement_animal_list_cancel_advanced_filters(live_server, page: Page):
    clinique = EvenementAnimalFactory(context_suspicion=ContexteSuspicion.CLINIQUE)
    analytique = EvenementAnimalFactory(context_suspicion=ContexteSuspicion.ANALYTIQUE)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"Contexte de la suspicion": "Clinique"})

    search_page.open_advanced_filters()
    search_page.advanced_field("Contexte de la suspicion").select_option(label="Analytique")
    search_page.advanced_field("N° DPE").fill("123")
    search_page.cancel_advanced_filters()

    expect(search_page.row(clinique.numero)).to_be_visible()
    expect(search_page.row(analytique.numero)).to_have_count(0)

    search_page.open_advanced_filters()
    expect(search_page.advanced_field("Contexte de la suspicion")).to_have_value(ContexteSuspicion.CLINIQUE)
    expect(search_page.advanced_field("N° DPE")).to_be_empty()


def test_reset_button_clears_advanced_filters(live_server, page: Page):
    clinique = EvenementAnimalFactory(context_suspicion=ContexteSuspicion.CLINIQUE)
    analytique = EvenementAnimalFactory(context_suspicion=ContexteSuspicion.ANALYTIQUE)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.search_with_advanced_filters({"Contexte de la suspicion": "Clinique"})
    expect(search_page.row(analytique.numero)).to_have_count(0)

    search_page.reset_search()

    expect(search_page.row(clinique.numero)).to_be_visible()
    expect(search_page.row(analytique.numero)).to_be_visible()
    expect(search_page.advanced_filters_button).to_have_text("Filtres avancés")
    search_page.open_advanced_filters()
    expect(search_page.advanced_field("Contexte de la suspicion")).to_have_value("")
