from django.urls import reverse
from playwright.sync_api import Page, expect
from pytest_django.asserts import assertRedirects

from core.factories import ContactAgentFactory, ContactStructureFactory, StructureFactory
from core.models import LienLibre
from ssa.constants import Source, TypeEvenement, PretAManger, SourceInvestigationCasHumain
from ssa.factories import EtablissementFactory, EvenementProduitFactory, InvestigationCasHumainFactory
from ssa.models import EvenementProduit, TemperatureConservation
from ssa.models.evenement_produit import ActionEngagees
from ssa.tests.pages import EvenementProduitListPage


def test_old_url_redirects(client):
    response = client.get(reverse("ssa:evenement-produit-liste"))
    assertRedirects(response, reverse("ssa:evenements-liste"), status_code=301)


def test_list_table_order(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(numero_annee=2025, numero_evenement=2)
    EvenementProduitFactory(numero_annee=2025, numero_evenement=1)
    InvestigationCasHumainFactory(numero_annee=2025, numero_evenement=22)
    InvestigationCasHumainFactory(numero_annee=2024, numero_evenement=22)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    assert search_page.numero_cell(line_index=1).text_content() == "A-2025.22"
    assert search_page.numero_cell(line_index=2).text_content() == "A-2025.2"
    assert search_page.numero_cell(line_index=3).text_content() == "A-2025.1"
    assert search_page.numero_cell(line_index=4).text_content() == "A-2024.22"


def test_list_filtered_by_visibilite(live_server, mocked_authentification_user, page: Page):
    evenement_1 = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON, createur=StructureFactory())
    evenement_2 = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS, createur=StructureFactory())
    evenement_3 = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON)
    evenement_4 = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    evenement_5 = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON, createur=StructureFactory())
    evenement_6 = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS, createur=StructureFactory())
    evenement_7 = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON)
    evenement_8 = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    expect(page.get_by_text(evenement_1.numero)).not_to_be_visible()
    expect(page.get_by_text(evenement_2.numero)).to_be_visible()
    expect(page.get_by_text(evenement_3.numero)).to_be_visible()
    expect(page.get_by_text(evenement_4.numero)).to_be_visible()

    expect(page.get_by_text(evenement_5.numero)).not_to_be_visible()
    expect(page.get_by_text(evenement_6.numero)).to_be_visible()
    expect(page.get_by_text(evenement_7.numero)).to_be_visible()
    expect(page.get_by_text(evenement_8.numero)).to_be_visible()


def test_row_content(live_server, mocked_authentification_user, page: Page):
    evenement = EvenementProduitFactory()
    other_structure = StructureFactory()
    LienLibre.objects.create(
        related_object_1=evenement, related_object_2=EvenementProduitFactory(createur=other_structure)
    )
    LienLibre.objects.create(
        related_object_1=evenement, related_object_2=EvenementProduitFactory(createur=other_structure)
    )
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    assert search_page.numero_cell().text_content() == evenement.numero
    assert search_page.date_creation_cell().text_content() == evenement.date_creation.strftime("%d/%m/%Y")
    assert search_page.description_cell().inner_text() == evenement.description
    assert search_page.type_evenement_cell().text_content() == evenement.get_type_evenement_display()
    assert search_page.createur_cell().text_content() == mocked_authentification_user.agent.structure.libelle
    assert search_page.etat_cell().text_content() == "Brouillon"


def test_list_can_filter_by_numero(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(numero_annee=2025, numero_evenement=2)
    InvestigationCasHumainFactory(numero_annee=2025, numero_evenement=1)
    EvenementProduitFactory(numero_annee=2024, numero_evenement=22)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.numero_field.fill("2025")
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "A-2025.2"
    expect(search_page.page.get_by_text("2024.22")).not_to_be_visible()


def test_list_can_filter_by_numero_rasff(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(numero_rasff=123456, numero_annee=2025, numero_evenement=2)
    EvenementProduitFactory(numero_rasff=987654, numero_annee=2025, numero_evenement=1)
    investigation = InvestigationCasHumainFactory()
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.numero_rasff_field.fill("123456")
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "A-2025.2"
    expect(search_page.page.get_by_text("2025.1")).not_to_be_visible()
    expect(page.get_by_text(investigation.numero)).not_to_be_visible()


def test_list_can_filter_by_type_evenement(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(
        type_evenement=TypeEvenement.ALERTE_PRODUIT_NATIONALE, numero_annee=2025, numero_evenement=2
    )
    EvenementProduitFactory(type_evenement=TypeEvenement.NON_ALERTE, numero_annee=2025, numero_evenement=1)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.type_evenement_select.select_option(TypeEvenement.NON_ALERTE)
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "A-2025.1"
    expect(search_page.page.get_by_text("2025.2")).not_to_be_visible()


def test_list_can_filter_by_type_evenement_for_investigation_cas_humain(
    live_server, mocked_authentification_user, page: Page
):
    EvenementProduitFactory(
        type_evenement=TypeEvenement.ALERTE_PRODUIT_NATIONALE, numero_annee=2025, numero_evenement=2
    )
    InvestigationCasHumainFactory(numero_annee=2025, numero_evenement=1)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.type_evenement_select.select_option("Investigation de cas humain")
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "A-2025.1"
    expect(search_page.page.get_by_text("2025.2")).not_to_be_visible()


def test_list_can_filter_by_source(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(
        source=Source.TOUT_DROIT, type_evenement=TypeEvenement.NON_ALERTE, numero_annee=2025, numero_evenement=2
    )
    EvenementProduitFactory(
        source=Source.AUTOCONTROLE_NOTIFIE_PRODUIT,
        type_evenement=TypeEvenement.NON_ALERTE,
        numero_annee=2025,
        numero_evenement=1,
    )
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.source_select.select_option(Source.TOUT_DROIT)
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "A-2025.2"
    expect(search_page.page.get_by_text("2025.1")).not_to_be_visible()


def test_list_can_filter_by_source_for_investigation_cas_humain(live_server, mocked_authentification_user, page: Page):
    InvestigationCasHumainFactory(
        source=SourceInvestigationCasHumain.DO_LISTERIOSE, numero_annee=2025, numero_evenement=2
    )
    InvestigationCasHumainFactory(
        source=SourceInvestigationCasHumain.CAS_GROUPES,
        numero_annee=2025,
        numero_evenement=1,
    )
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.source_select.select_option(SourceInvestigationCasHumain.DO_LISTERIOSE)
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "A-2025.2"
    expect(search_page.page.get_by_text("2025.1")).not_to_be_visible()


def test_list_can_filter_by_common_source(live_server, mocked_authentification_user, page: Page):
    InvestigationCasHumainFactory(
        source=SourceInvestigationCasHumain.SIGNALEMENT_AUTRE, numero_annee=2025, numero_evenement=2
    )
    InvestigationCasHumainFactory(
        source=SourceInvestigationCasHumain.CAS_GROUPES,
        numero_annee=2025,
        numero_evenement=1,
    )
    EvenementProduitFactory(source=Source.AUTRE, numero_annee=2025, numero_evenement=3)
    EvenementProduitFactory(source=Source.TOUT_DROIT, numero_annee=2025, numero_evenement=4)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.source_select.select_option(SourceInvestigationCasHumain.SIGNALEMENT_AUTRE)
    search_page.submit_search()
    expect(search_page.page.get_by_text("2025.1")).not_to_be_visible()
    expect(search_page.page.get_by_text("2025.2")).to_be_visible()
    expect(search_page.page.get_by_text("2025.3")).to_be_visible()
    expect(search_page.page.get_by_text("2025.4")).not_to_be_visible()


def test_list_can_filter_by_date(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(date_creation="2024-06-18", numero_annee=2025, numero_evenement=3)
    EvenementProduitFactory(date_creation="2024-06-19", numero_annee=2025, numero_evenement=2)
    EvenementProduitFactory(date_creation="2024-06-22", numero_annee=2025, numero_evenement=1)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.start_date_field.fill("2024-06-19")
    search_page.end_date_field.fill("2024-06-20")
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "A-2025.2"
    expect(search_page.page.get_by_text("2025.1")).not_to_be_visible()
    expect(search_page.page.get_by_text("2025.3")).not_to_be_visible()


def test_list_can_reset_form_after_search(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(numero_annee=2024, numero_evenement=22)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.numero_field.fill("2025")
    search_page.submit_search()
    expect(search_page.page.get_by_text("2024.22")).not_to_be_visible()

    search_page.reset_search()
    search_page.page.wait_for_timeout(600)
    expect(search_page.page.get_by_text("2024.22")).to_be_visible()
    expect(search_page.numero_field).to_have_value("")


def test_compteur_fiche(live_server, page: Page):
    nb_evenements = 101
    EvenementProduitFactory.create_batch(nb_evenements)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    expect(page.get_by_text(f"100 sur un total de {nb_evenements}", exact=True)).to_be_visible()
    page.get_by_role("link", name="Dernière page").click()
    expect(page.get_by_text(f"1 sur un total de {nb_evenements}", exact=True)).to_be_visible()


def test_list_can_filter_with_free_search(live_server, mocked_authentification_user, page: Page):
    evenement_1 = EvenementProduitFactory(description="Morbier")
    evenement_2 = EvenementProduitFactory(denomination="Morbier")
    evenement_3 = EvenementProduitFactory(marque="Morbier")
    evenement_4 = EvenementProduitFactory(evaluation="Morbier")
    evenement_5 = EvenementProduitFactory(lots="Morbier")
    evenement_6 = EvenementProduitFactory(description_complementaire="Morbier")
    evenement_7 = EvenementProduitFactory()
    EtablissementFactory(raison_sociale="Morbier", evenement_produit=evenement_7)
    evenement_8 = EvenementProduitFactory()
    evenement_9 = EvenementProduitFactory()
    evenement_10 = EvenementProduitFactory()
    EtablissementFactory(enseigne_usuelle="Morbier", evenement_produit=evenement_10)
    evenement_11 = InvestigationCasHumainFactory()
    evenement_12 = InvestigationCasHumainFactory()
    EtablissementFactory(enseigne_usuelle="Morbier", investigation_cas_humain=evenement_12)
    evenement_13 = EvenementProduitFactory(precision_danger="Morbier")
    evenement_14 = InvestigationCasHumainFactory(precision_danger="Morbier")
    evenement_15 = InvestigationCasHumainFactory(evaluation="Morbier")

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.full_text_field.fill("Morbier")
    search_page.submit_search()
    expect(search_page.page.get_by_text(evenement_1.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_2.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_3.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_4.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_5.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_6.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_7.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_8.numero)).not_to_be_visible()
    expect(search_page.page.get_by_text(evenement_9.numero)).not_to_be_visible()
    expect(search_page.page.get_by_text(evenement_10.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_11.numero)).not_to_be_visible()
    expect(search_page.page.get_by_text(evenement_12.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_13.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_14.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_15.numero)).to_be_visible()


def test_more_filters_interactions(live_server, page: Page):
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.reference_souches.fill("Test")
    search_page.reference_clusters.fill("Test")
    search_page.add_filters()

    expect(search_page.filter_counter).to_be_visible()
    expect(search_page.filter_counter).to_have_text("2")

    search_page.open_sidebar()
    search_page.numeros_rappel_conso.fill("Test")
    search_page.add_filters()

    expect(search_page.filter_counter).to_be_visible()
    expect(search_page.filter_counter).to_have_text("3")

    search_page.open_sidebar()
    search_page.reset_more_filters()
    search_page.close_sidebar()
    expect(search_page.filter_counter).not_to_be_visible()


def test_more_filters_counter_after_search_is_done(live_server, page: Page):
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    initial_timestamp = page.evaluate("performance.timing.navigationStart")
    search_page.open_sidebar()
    search_page.reference_souches.fill("Test")
    search_page.reference_clusters.fill("Test")
    search_page.add_filters()

    expect(search_page.filter_counter).to_be_visible()
    expect(search_page.filter_counter).to_have_text("2")
    search_page.submit_search()

    page.wait_for_function(f"performance.timing.navigationStart > {initial_timestamp}")
    expect(search_page.filter_counter).to_be_visible()
    expect(search_page.filter_counter).to_have_text("2")


def test_can_filter_by_etat(live_server, mocked_authentification_user, page: Page):
    to_be_found = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    to_be_found_2 = InvestigationCasHumainFactory(etat=EvenementProduit.Etat.EN_COURS)
    not_to_be_found_1 = EvenementProduitFactory()
    not_to_be_found_2 = EvenementProduitFactory(etat=EvenementProduit.Etat.CLOTURE)
    not_to_be_found_3 = InvestigationCasHumainFactory()
    not_to_be_found_4 = InvestigationCasHumainFactory(etat=EvenementProduit.Etat.CLOTURE)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.etat.select_option("En cours")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(to_be_found_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_4.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_aliments_animaux(live_server, page: Page):
    to_be_found = EvenementProduitFactory(aliments_animaux=True)
    not_to_be_found_1 = EvenementProduitFactory(aliments_animaux=False)
    not_to_be_found_2 = EvenementProduitFactory(aliments_animaux=None)
    not_to_be_found_3 = InvestigationCasHumainFactory()

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.aliments_animaux.select_option("Oui")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_temperature_conservation(live_server, mocked_authentification_user, page: Page):
    to_be_found = EvenementProduitFactory(temperature_conservation=TemperatureConservation.SURGELE)
    not_to_be_found_1 = EvenementProduitFactory(temperature_conservation=TemperatureConservation.REFRIGERE)
    not_to_be_found_2 = EvenementProduitFactory(temperature_conservation=TemperatureConservation.TEMPERATURE_AMBIANTE)
    not_to_be_found_3 = InvestigationCasHumainFactory()

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.temperature_conservation.select_option("Surgelé")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_produit_pret_a_manger(live_server, mocked_authentification_user, page: Page):
    to_be_found = EvenementProduitFactory(bacterie=True, produit_pret_a_manger=PretAManger.OUI)
    not_to_be_found_1 = EvenementProduitFactory(bacterie=True, produit_pret_a_manger=PretAManger.NON)
    not_to_be_found_2 = EvenementProduitFactory(bacterie=True, produit_pret_a_manger=PretAManger.SANS_OBJET)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.pret_a_manger.select_option("Oui")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_reference_souches(live_server, mocked_authentification_user, page: Page):
    to_be_found = EvenementProduitFactory(reference_souches="FOO")
    not_to_be_found_1 = EvenementProduitFactory(reference_souches="BAR")
    not_to_be_found_2 = EvenementProduitFactory(reference_souches="BUZZ")
    not_to_be_found_3 = InvestigationCasHumainFactory()

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.reference_souches.fill("FOO")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_reference_clusters(live_server, mocked_authentification_user, page: Page):
    to_be_found = EvenementProduitFactory(reference_clusters="FOO")
    not_to_be_found_1 = EvenementProduitFactory(reference_clusters="BAR")
    not_to_be_found_2 = EvenementProduitFactory(reference_clusters="BUZZ")
    not_to_be_found_3 = InvestigationCasHumainFactory()

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.reference_clusters.fill("FOO")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_actions_engagees(live_server, mocked_authentification_user, page: Page):
    to_be_found = EvenementProduitFactory(actions_engagees=ActionEngagees.RETRAIT)
    not_to_be_found_1 = EvenementProduitFactory(actions_engagees=ActionEngagees.PAS_DE_MESURE)
    not_to_be_found_2 = EvenementProduitFactory(actions_engagees=ActionEngagees.RETRAIT_RAPPEL)
    not_to_be_found_3 = EvenementProduitFactory(actions_engagees=ActionEngagees.RETRAIT_RAPPEL_CP)
    not_to_be_found_4 = InvestigationCasHumainFactory()

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.actions_engagees.select_option("Retrait du marché sans information des consommateurs")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_4.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_numeros_rappel_conso(live_server, mocked_authentification_user, page: Page):
    to_be_found_1 = EvenementProduitFactory(numeros_rappel_conso=["2024-10-1000", "2024-10-1001"])
    to_be_found_2 = EvenementProduitFactory(numeros_rappel_conso=["2024-10-1005", "2024-10-1000"])
    not_to_be_found_1 = EvenementProduitFactory(numeros_rappel_conso=[])
    not_to_be_found_2 = EvenementProduitFactory(numeros_rappel_conso=["2023-20-2000"])
    not_to_be_found_3 = InvestigationCasHumainFactory()

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.numeros_rappel_conso.fill("2024-10-1000")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found_1.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(to_be_found_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_numero_agrement(live_server, mocked_authentification_user, page: Page):
    to_be_found = EtablissementFactory(numero_agrement="123.11.111")
    to_be_found_2 = EtablissementFactory(
        numero_agrement="123.11.111", investigation_cas_humain=InvestigationCasHumainFactory()
    )
    not_to_be_found_1 = EtablissementFactory(numero_agrement="")
    not_to_be_found_2 = EtablissementFactory(numero_agrement="124.11.111")

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.numero_agrement.fill("123.11.111")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.evenement_produit.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(to_be_found_2.investigation_cas_humain.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.evenement_produit.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.evenement_produit.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_commune(live_server, mocked_authentification_user, page: Page):
    to_be_found = EtablissementFactory(commune="Paris")
    to_be_found_2 = EtablissementFactory(commune="Paris", investigation_cas_humain=InvestigationCasHumainFactory())
    not_to_be_found_1 = EtablissementFactory(commune="")
    not_to_be_found_2 = EtablissementFactory(commune="Bordeaux")

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.commune.fill("Paris")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.evenement_produit.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(to_be_found_2.investigation_cas_humain.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.evenement_produit.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.evenement_produit.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_siret(live_server, mocked_authentification_user, page: Page):
    to_be_found = EtablissementFactory(siret="12345678912345")
    to_be_found_2 = EtablissementFactory(
        siret="12345678912345", investigation_cas_humain=InvestigationCasHumainFactory()
    )
    not_to_be_found_1 = EtablissementFactory(siret="")
    not_to_be_found_2 = EtablissementFactory(siret="9" * 14)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.siret.fill("12345678")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.evenement_produit.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(to_be_found_2.investigation_cas_humain.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.evenement_produit.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.evenement_produit.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_departement(live_server, ensure_departements, mocked_authentification_user, page: Page):
    cantal, aveyron, *_ = ensure_departements("Cantal", "Aveyron")
    to_be_found = EtablissementFactory(departement=cantal)
    to_be_found_2 = EtablissementFactory(departement=cantal, investigation_cas_humain=InvestigationCasHumainFactory())
    not_to_be_found_1 = EtablissementFactory(departement=aveyron)
    not_to_be_found_2 = EtablissementFactory(departement=None)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.departement.select_option("15 - Cantal")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.evenement_produit.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(to_be_found_2.investigation_cas_humain.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.evenement_produit.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.evenement_produit.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_pays(live_server, mocked_authentification_user, page: Page):
    to_be_found = EtablissementFactory(pays="FR")
    to_be_found_2 = EtablissementFactory(pays="FR", investigation_cas_humain=InvestigationCasHumainFactory())
    not_to_be_found_1 = EtablissementFactory(pays="BE")
    not_to_be_found_2 = EtablissementFactory(pays="")

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.pays.select_option("France")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.evenement_produit.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(to_be_found_2.investigation_cas_humain.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.evenement_produit.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.evenement_produit.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_categorie_produit(live_server, mocked_authentification_user, page: Page):
    to_be_found = EvenementProduitFactory(categorie_produit="VH - Bovin")
    not_to_be_found_1 = EvenementProduitFactory(categorie_produit="PC - Céphalopode")
    not_to_be_found_2 = EvenementProduitFactory(categorie_produit="Escargot")
    not_to_be_found_3 = InvestigationCasHumainFactory()

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.set_categorie_produit("Produit carné > Viande hachée > VH - Bovin")
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_categorie_produit_found_by_parent(live_server, mocked_authentification_user, page: Page):
    to_be_found = EvenementProduitFactory(categorie_produit="VH - Bovin")
    not_to_be_found_1 = EvenementProduitFactory(categorie_produit="PC - Céphalopode")
    not_to_be_found_2 = EvenementProduitFactory(categorie_produit="Escargot")
    not_to_be_found_3 = InvestigationCasHumainFactory()

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.set_categorie_produit("Produit carné > Viande hachée")
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_categorie_danger(live_server, mocked_authentification_user, page: Page):
    to_be_found = EvenementProduitFactory(categorie_danger="Salmonella dublin")
    not_to_be_found_1 = EvenementProduitFactory(categorie_danger="Listeria")
    not_to_be_found_2 = EvenementProduitFactory(categorie_danger="Staphylococcus")
    not_to_be_found_3 = InvestigationCasHumainFactory()

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.set_categorie_danger("Bactérie > Salmonella > Salmonella dublin")
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_with_free_links(live_server, mocked_authentification_user, page: Page):
    to_be_found = EvenementProduitFactory(numero_annee=2025, numero_evenement=2)
    linked_evenement = EvenementProduitFactory(numero_annee=2025, numero_evenement=1)
    linked_investigation = InvestigationCasHumainFactory(numero_annee=2025, numero_evenement=3)
    LienLibre.objects.create(related_object_1=linked_evenement, related_object_2=to_be_found)
    LienLibre.objects.create(related_object_1=linked_investigation, related_object_2=to_be_found)

    not_to_be_found_1 = EvenementProduitFactory(numero_annee=2024, numero_evenement=2)
    not_to_be_found_2 = EvenementProduitFactory(numero_annee=2024, numero_evenement=1)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.numero_field.fill("2025.2")
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(linked_evenement.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(linked_investigation.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()

    search_page.numero_field.fill("2025.2")
    search_page.with_links.check()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(linked_evenement.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(linked_investigation.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()


def test_search_with_structure_contact(live_server, page: Page, choice_js_fill_from_element):
    evenement_1 = EvenementProduitFactory()
    evenement_2 = EvenementProduitFactory()
    evenement_3 = EvenementProduitFactory()
    contact_structure = ContactStructureFactory(with_one_active_agent=True)
    evenement_2.contacts.add(contact_structure)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.set_structure_filter(str(contact_structure), choice_js_fill_from_element)
    search_page.submit_search()

    expect(page.get_by_text(evenement_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(evenement_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(evenement_3.numero, exact=True)).not_to_be_visible()


def test_search_with_agent_contact(live_server, page: Page, choice_js_fill, choice_js_fill_from_element):
    evenement_1 = EvenementProduitFactory()
    evenement_2 = EvenementProduitFactory()
    evenement_3 = InvestigationCasHumainFactory()
    contact_agent = ContactAgentFactory(with_active_agent=True)
    evenement_2.contacts.add(contact_agent)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    search_page.set_agent_filter(str(contact_agent), choice_js_fill_from_element)
    search_page.submit_search()

    expect(page.get_by_text(evenement_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(evenement_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(evenement_3.numero, exact=True)).not_to_be_visible()


def test_number_of_total_items(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON, createur=StructureFactory())
    EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON)
    InvestigationCasHumainFactory(etat=EvenementProduit.Etat.BROUILLON)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()
    expect(page.get_by_text("3 sur un total de 3", exact=True)).to_be_visible()

    search_page.open_sidebar()
    search_page.etat.select_option("En cours")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text("1 sur un total de 3", exact=True)).to_be_visible()
