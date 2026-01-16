from playwright.sync_api import Page, expect

from core.factories import ContactStructureFactory, ContactAgentFactory
from core.models import Departement, LienLibre
from ssa.constants import CategorieDanger, CategorieProduit
from tiac.constants import DangersSyndromiques, SuspicionConclusion
from tiac.factories import (
    EvenementSimpleFactory,
    InvestigationTiacFactory,
    EtablissementFactory,
    RepasSuspectFactory,
    AlimentSuspectFactory,
    AnalyseAlimentaireFactory,
)
from tiac.models import EvenementSimple, InvestigationTiac, InvestigationFollowUp
from tiac.tests.pages import EvenementListPage


def test_list_table_order(live_server, mocked_authentification_user, page: Page):
    EvenementSimpleFactory(numero_annee=2025, numero_evenement=2)
    EvenementSimpleFactory(numero_annee=2025, numero_evenement=1)
    InvestigationTiacFactory(numero_annee=2025, numero_evenement=22)
    InvestigationTiacFactory(numero_annee=2024, numero_evenement=22)
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    assert search_page.numero_cell(line_index=1).text_content() == "T-2025.22"
    assert search_page.numero_cell(line_index=2).text_content() == "T-2025.2"
    assert search_page.numero_cell(line_index=3).text_content() == "T-2025.1"
    assert search_page.numero_cell(line_index=4).text_content() == "T-2024.22"


def test_row_content_evenement_simple(live_server, mocked_authentification_user, page: Page):
    evenement: EvenementSimple = EvenementSimpleFactory()
    etablissement = EtablissementFactory(evenement_simple=evenement)
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    assert search_page.numero_cell().text_content() == evenement.numero
    assert search_page.createur_cell().text_content() == mocked_authentification_user.agent.structure.libelle
    assert search_page.date_reception_cell().text_content() == evenement.date_reception.strftime("%d/%m/%Y")
    assert search_page.etablissement_cell().text_content().strip().replace("\n", "") == etablissement.raison_sociale
    assert search_page.malades_cell().text_content() == str(evenement.nb_sick_persons)
    assert search_page.type_cell().text_content() == f"Enr. simple / {evenement.get_follow_up_display()}"
    assert search_page.conclusion_cell().text_content() == "-"
    assert search_page.danger_cell().text_content().strip() == "-"
    assert search_page.etat_cell().text_content() == "Brouillon"


def test_row_content_investigation_tiac(live_server, mocked_authentification_user, page: Page):
    evenement: InvestigationTiac = InvestigationTiacFactory(follow_up=InvestigationFollowUp.INVESTIGATION_COORDONNEE)
    etablissement = EtablissementFactory(investigation=evenement)
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    assert search_page.numero_cell().text_content() == evenement.numero
    assert search_page.createur_cell().text_content() == mocked_authentification_user.agent.structure.libelle
    assert search_page.date_reception_cell().text_content() == evenement.date_reception.strftime("%d/%m/%Y")
    assert search_page.etablissement_cell().text_content().strip().replace("\n", "") == etablissement.raison_sociale
    assert search_page.malades_cell().text_content() == str(evenement.nb_sick_persons)
    assert search_page.type_cell().text_content() == "Invest. coord. / MUS informée"
    assert search_page.conclusion_cell().text_content() == evenement.get_suspicion_conclusion_display()
    assert search_page.danger_cell().text_content() == evenement.short_conclusion_selected_hazard or "-"
    assert search_page.etat_cell().text_content() == "Brouillon"


def test_list_can_filter_by_numero(live_server, mocked_authentification_user, page: Page):
    EvenementSimpleFactory(numero_annee=2025, numero_evenement=2)
    InvestigationTiacFactory(numero_annee=2025, numero_evenement=1)
    EvenementSimpleFactory(numero_annee=2024, numero_evenement=2)
    InvestigationTiacFactory(numero_annee=2024, numero_evenement=22)
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    search_page.numero_field.fill("2025")
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "T-2025.2"
    assert search_page.numero_cell(line_index=2).text_content() == "T-2025.1"
    expect(search_page.page.get_by_text("2024.22")).not_to_be_visible()
    expect(search_page.page.get_by_text("2024.2")).not_to_be_visible()


def test_list_can_filter_by_date(live_server, mocked_authentification_user, page: Page):
    EvenementSimpleFactory(date_reception="2024-06-18", numero_annee=2025, numero_evenement=3)
    InvestigationTiacFactory(date_reception="2024-06-19", numero_annee=2025, numero_evenement=2)
    EvenementSimpleFactory(date_reception="2024-06-22", numero_annee=2025, numero_evenement=1)
    InvestigationTiacFactory(date_reception="2024-06-03", numero_annee=2025, numero_evenement=4)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    search_page.start_date_field.fill("2024-06-17")
    search_page.end_date_field.fill("2024-06-20")
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "T-2025.3"
    assert search_page.numero_cell(line_index=2).text_content() == "T-2025.2"
    expect(search_page.page.get_by_text("2025.1")).not_to_be_visible()
    expect(search_page.page.get_by_text("2025.4")).not_to_be_visible()


def test_search_with_structure_contact(live_server, page: Page, choice_js_fill_from_element):
    evenement_1 = EvenementSimpleFactory(numero_annee=2024)
    evenement_2 = InvestigationTiacFactory(numero_annee=2025)
    evenement_3 = EvenementSimpleFactory(numero_annee=2026)
    evenement_4 = InvestigationTiacFactory(numero_annee=2027)
    contact_structure = ContactStructureFactory(with_one_active_agent=True)
    evenement_1.contacts.add(contact_structure)
    evenement_2.contacts.add(contact_structure)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.set_structure_filter(str(contact_structure), choice_js_fill_from_element)
    search_page.submit_search()

    expect(page.get_by_text(evenement_1.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(evenement_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(evenement_3.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(evenement_4.numero, exact=True)).not_to_be_visible()


def test_search_with_agent_contact(live_server, page: Page, choice_js_fill, choice_js_fill_from_element):
    evenement_1 = EvenementSimpleFactory(numero_annee=2000)
    evenement_2 = InvestigationTiacFactory(numero_annee=2001)
    evenement_3 = EvenementSimpleFactory(numero_annee=2002)
    evenement_4 = InvestigationTiacFactory(numero_annee=2003)
    contact_agent = ContactAgentFactory(with_active_agent=True)
    evenement_1.contacts.add(contact_agent)
    evenement_2.contacts.add(contact_agent)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.set_agent_filter(str(contact_agent), choice_js_fill_from_element)
    search_page.submit_search()

    expect(page.get_by_text(evenement_1.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(evenement_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(evenement_3.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(evenement_4.numero, exact=True)).not_to_be_visible()


def test_search_with_conclusion(live_server, page: Page):
    evenement_1 = EvenementSimpleFactory(numero_annee=2025)
    evenement_2 = InvestigationTiacFactory(numero_annee=2024, suspicion_conclusion=SuspicionConclusion.CONFIRMED)
    evenement_3 = InvestigationTiacFactory(numero_annee=2023, suspicion_conclusion=None)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.conclusion_field.select_option("TIAC à agent confirmé")
    search_page.submit_search()

    expect(page.get_by_text(evenement_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(evenement_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(evenement_3.numero, exact=True)).not_to_be_visible()


def test_search_with_selected_hazard(live_server, page: Page, choice_js_fill_from_element_with_value):
    evenement_1 = EvenementSimpleFactory(numero_annee=2025)
    evenement_2 = InvestigationTiacFactory(
        numero_annee=2024,
        suspicion_conclusion=SuspicionConclusion.SUSPECTED,
        selected_hazard=[DangersSyndromiques.INTOXINATION_BACILLUS],
    )
    evenement_3 = InvestigationTiacFactory(numero_annee=2023, suspicion_conclusion=None)
    evenement_4 = InvestigationTiacFactory(numero_annee=2022, suspicion_conclusion=SuspicionConclusion.DISCARDED)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.select_hazard("Bacillus Cereus - Staphylococcus Aureus")
    search_page.submit_search()

    expect(page.get_by_text(evenement_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(evenement_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(evenement_3.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(evenement_4.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_commune(live_server, mocked_authentification_user, page: Page):
    to_be_found = EtablissementFactory(commune="Paris")
    not_to_be_found_1 = EtablissementFactory(commune="")
    not_to_be_found_2 = EtablissementFactory(commune="Bordeaux")

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.commune.fill("Paris")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.evenement_simple.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.evenement_simple.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.evenement_simple.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_siret(live_server, mocked_authentification_user, page: Page):
    to_be_found = EtablissementFactory(siret="12345678912345")
    not_to_be_found_1 = EtablissementFactory(siret="")
    not_to_be_found_2 = EtablissementFactory(siret="9" * 14)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.siret.fill("12345678")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.evenement_simple.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.evenement_simple.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.evenement_simple.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_departement(live_server, ensure_departements, mocked_authentification_user, page: Page):
    ensure_departements("Cantal", "Aveyron")
    to_be_found = EtablissementFactory(departement=Departement.objects.get(nom="Cantal"))
    not_to_be_found_1 = EtablissementFactory(departement=Departement.objects.get(nom="Aveyron"))
    not_to_be_found_2 = EtablissementFactory(departement=None)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.departement.select_option("15 - Cantal")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.evenement_simple.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.evenement_simple.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.evenement_simple.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_pays(live_server, mocked_authentification_user, page: Page):
    to_be_found = EtablissementFactory(pays="FR")
    not_to_be_found_1 = EtablissementFactory(pays="BE")
    not_to_be_found_2 = EtablissementFactory(pays="")

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.pays.select_option("France")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.evenement_simple.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.evenement_simple.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.evenement_simple.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_etat(live_server, mocked_authentification_user, page: Page):
    to_be_found_1 = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS, numero_annee=2020)
    to_be_found_2 = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS, numero_annee=2021)
    not_to_be_found_1 = InvestigationTiacFactory(numero_annee=2022)
    not_to_be_found_2 = EvenementSimpleFactory(etat=EvenementSimple.Etat.CLOTURE, numero_annee=2023)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.etat.select_option("En cours")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found_1.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(to_be_found_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_numero_sivss(live_server, mocked_authentification_user, page: Page):
    to_be_found_1 = InvestigationTiacFactory(numero_annee=2020, numero_sivss="111111")
    not_to_be_found_1 = EvenementSimpleFactory(numero_annee=2021)
    not_to_be_found_2 = InvestigationTiacFactory(numero_annee=2022, numero_sivss="")

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.numero_sivss.fill("111111")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found_1.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_nb_sick_persons(live_server, mocked_authentification_user, page: Page):
    to_be_found_1 = InvestigationTiacFactory(numero_annee=2020, nb_sick_persons=6)
    to_be_found_2 = EvenementSimpleFactory(numero_annee=2021, nb_sick_persons=8)
    not_to_be_found_1 = EvenementSimpleFactory(numero_annee=2022, nb_sick_persons=0)
    not_to_be_found_2 = InvestigationTiacFactory(numero_annee=2023, nb_sick_persons=50)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.nb_sick_persons.select_option("[6-10]")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found_1.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(to_be_found_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_nb_dead_persons(live_server, mocked_authentification_user, page: Page):
    to_be_found_1 = InvestigationTiacFactory(numero_annee=2020, nb_dead_persons=6)
    not_to_be_found_1 = InvestigationTiacFactory(numero_annee=2022, nb_dead_persons=0)
    not_to_be_found_2 = EvenementSimpleFactory(numero_annee=2023)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.nb_dead_persons.select_option("[1+]")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found_1.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_repas_nb_particpants(live_server, mocked_authentification_user, page: Page):
    to_be_found_1 = InvestigationTiacFactory(numero_annee=2020)
    RepasSuspectFactory(investigation=to_be_found_1, nombre_participant="environ 200")
    not_to_be_found_1 = InvestigationTiacFactory(numero_annee=2022)
    RepasSuspectFactory(investigation=not_to_be_found_1, nombre_participant="une cinquantaine")
    not_to_be_found_2 = EvenementSimpleFactory(numero_annee=2023)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.nb_participants.fill("200")
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found_1.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_danger_syndromique(
    live_server, mocked_authentification_user, page: Page, choice_js_fill_from_element_with_value
):
    to_be_found_1 = InvestigationTiacFactory(
        numero_annee=2020, danger_syndromiques_suspectes=[DangersSyndromiques.HISTAMINE, DangersSyndromiques.AUTRE]
    )
    not_to_be_found_1 = InvestigationTiacFactory(
        numero_annee=2022, danger_syndromiques_suspectes=[DangersSyndromiques.BACTERIE_INTESTINALE]
    )
    not_to_be_found_2 = InvestigationTiacFactory(numero_annee=2023, danger_syndromiques_suspectes=[])
    not_to_be_found_3 = InvestigationTiacFactory(
        numero_annee=2024,
        danger_syndromiques_suspectes=[DangersSyndromiques.HISTAMINE, DangersSyndromiques.BACTERIE_INTESTINALE],
    )

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.select_danger_syndromiques(
        [DangersSyndromiques.HISTAMINE, DangersSyndromiques.AUTRE], choice_js_fill_from_element_with_value
    )
    search_page.add_filters()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found_1.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()

    expect(page.get_by_text(not_to_be_found_3.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_with_free_links(live_server, mocked_authentification_user, page: Page):
    to_be_found = InvestigationTiacFactory(numero_annee=2025, numero_evenement=2)
    linked_evenement = InvestigationTiacFactory(numero_annee=2025, numero_evenement=1)
    LienLibre.objects.create(related_object_1=linked_evenement, related_object_2=to_be_found)
    linked_evenement_2 = EvenementSimpleFactory(numero_annee=2025, numero_evenement=3)
    LienLibre.objects.create(related_object_1=linked_evenement_2, related_object_2=to_be_found)

    not_to_be_found_1 = InvestigationTiacFactory(numero_annee=2024, numero_evenement=2)
    not_to_be_found_2 = EvenementSimpleFactory(numero_annee=2024, numero_evenement=1)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.numero_field.fill("2025.2")
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(linked_evenement.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(linked_evenement_2.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()

    search_page.numero_field.fill("2025.2")
    search_page.with_links.check()
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(linked_evenement.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(linked_evenement_2.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()


def test_can_filter_by_follow_up(live_server, mocked_authentification_user, page: Page):
    to_be_found = InvestigationTiacFactory(
        numero_annee=2025, numero_evenement=2, follow_up=InvestigationFollowUp.INVESTIGATION_COORDONNEE
    )
    not_to_be_found_1 = InvestigationTiacFactory(
        numero_annee=2025, numero_evenement=1, follow_up=InvestigationFollowUp.INVESTIGATION_DD
    )
    not_to_be_found_2 = EvenementSimpleFactory(numero_annee=2025, numero_evenement=3)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.follow_up.select_option("Investigation TIAC / Investigation coordonnée / MUS informée")
    search_page.submit_search()

    expect(page.get_by_text(to_be_found.numero, exact=True)).to_be_visible()
    expect(page.get_by_text(not_to_be_found_1.numero, exact=True)).not_to_be_visible()
    expect(page.get_by_text(not_to_be_found_2.numero, exact=True)).not_to_be_visible()


def test_list_can_filter_with_free_search_investigation_tiac(live_server, mocked_authentification_user, page: Page):
    evenement_1 = InvestigationTiacFactory(contenu="Morbier")
    evenement_2 = InvestigationTiacFactory(precisions="Morbier")
    evenement_3 = InvestigationTiacFactory()
    EtablissementFactory(raison_sociale="Morbier", investigation=evenement_3)
    evenement_4 = InvestigationTiacFactory()
    EtablissementFactory(enseigne_usuelle="Morbier", investigation=evenement_4)

    evenement_5 = InvestigationTiacFactory()
    RepasSuspectFactory(investigation=evenement_5, denomination="Morbier")
    evenement_6 = InvestigationTiacFactory()
    RepasSuspectFactory(investigation=evenement_6, menu="Morbier")

    evenement_7 = InvestigationTiacFactory()
    AlimentSuspectFactory(investigation=evenement_7, simple=True, denomination="Morbier")
    evenement_8 = InvestigationTiacFactory()
    AlimentSuspectFactory(investigation=evenement_8, simple=True, description_produit="Morbier")
    evenement_9 = InvestigationTiacFactory()
    AlimentSuspectFactory(investigation=evenement_9, cuisine=True, description_composition="Morbier")

    evenement_10 = InvestigationTiacFactory()
    AnalyseAlimentaireFactory(investigation=evenement_10, reference_prelevement="Morbier")
    evenement_11 = InvestigationTiacFactory()
    AnalyseAlimentaireFactory(investigation=evenement_11, comments="Morbier")

    evenement_12 = InvestigationTiacFactory(conclusion_comment="Morbier")

    evenement_other_1 = InvestigationTiacFactory()
    evenement_other_2 = InvestigationTiacFactory()

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    search_page.full_text_field.fill("Morbier")
    search_page.submit_search()
    expect(search_page.page.get_by_text(evenement_1.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_2.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_3.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_4.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_5.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_6.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_7.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_8.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_9.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_10.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_11.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_12.numero, exact=True)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_other_1.numero, exact=True)).not_to_be_visible()
    expect(search_page.page.get_by_text(evenement_other_2.numero, exact=True)).not_to_be_visible()


def test_list_can_filter_with_free_search_evenement_simple(live_server, mocked_authentification_user, page: Page):
    evenement_1 = EvenementSimpleFactory(contenu="Morbier")
    evenement_2 = EvenementSimpleFactory()
    EtablissementFactory(raison_sociale="Morbier", evenement_simple=evenement_2)
    evenement_3 = EvenementSimpleFactory()
    EtablissementFactory(enseigne_usuelle="Morbier", evenement_simple=evenement_3)

    evenement_4 = EvenementSimpleFactory()
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    search_page.full_text_field.fill("Morbier")
    search_page.submit_search()
    expect(search_page.page.get_by_text(evenement_1.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_2.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_3.numero)).to_be_visible()
    expect(search_page.page.get_by_text(evenement_4.numero)).not_to_be_visible()


def test_list_can_filter_with_free_search_investigation_tiac_is_disctinct(
    live_server, mocked_authentification_user, page: Page
):
    evenement_3 = InvestigationTiacFactory()
    EtablissementFactory(raison_sociale="Morbier", investigation=evenement_3)
    RepasSuspectFactory(investigation=evenement_3)
    RepasSuspectFactory(investigation=evenement_3)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.full_text_field.fill("Morbier")
    search_page.submit_search()
    assert search_page.nb_lines == 1


def test_list_can_filter_by_agents_pathogenes(live_server, page: Page):
    EvenementSimpleFactory(numero_annee=2025, numero_evenement=3)
    InvestigationTiacFactory(
        agents_confirmes_ars=[CategorieDanger.BACILLUS_CEREUS], numero_annee=2025, numero_evenement=2
    )
    InvestigationTiacFactory(agents_confirmes_ars=[], numero_annee=2025, numero_evenement=4)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.set_agents_pathogenes_from_shortcut(CategorieDanger.BACILLUS_CEREUS)
    search_page.add_filters()
    search_page.submit_search()

    assert search_page.numero_cell().text_content() == "T-2025.2"
    expect(search_page.page.get_by_text("2025.3")).not_to_be_visible()
    expect(search_page.page.get_by_text("2025.4")).not_to_be_visible()


def test_list_can_filter_by_analyse_danger(live_server, page: Page):
    evenement_1 = InvestigationTiacFactory(numero_annee=2025, numero_evenement=3)
    AnalyseAlimentaireFactory(categorie_danger=[CategorieDanger.BACILLUS_CEREUS], investigation=evenement_1)
    _evenement_2 = InvestigationTiacFactory(numero_annee=2025, numero_evenement=2)
    evenement_3 = InvestigationTiacFactory(numero_annee=2025, numero_evenement=1)
    AnalyseAlimentaireFactory(categorie_danger=[], investigation=evenement_3)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.set_analyse_danger_from_shortcut(CategorieDanger.BACILLUS_CEREUS)
    search_page.add_filters()
    search_page.submit_search()

    assert search_page.numero_cell().text_content() == "T-2025.3"
    expect(search_page.page.get_by_text("2025.2")).not_to_be_visible()
    expect(search_page.page.get_by_text("2025.1")).not_to_be_visible()


def test_list_can_filter_by_aliment_categorie_produit(live_server, page: Page):
    evenement_1 = InvestigationTiacFactory(numero_annee=2025, numero_evenement=3)
    aliment = AlimentSuspectFactory(categorie_produit=CategorieProduit.ESCARGOT, simple=True, investigation=evenement_1)
    _evenement_2 = InvestigationTiacFactory(numero_annee=2025, numero_evenement=2)
    evenement_3 = InvestigationTiacFactory(numero_annee=2025, numero_evenement=1)
    AlimentSuspectFactory(categorie_produit=[], simple=True, investigation=evenement_3)

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.open_sidebar()
    search_page.set_categorie_produit(aliment)
    search_page.add_filters()
    search_page.submit_search()

    assert search_page.numero_cell().text_content() == "T-2025.3"
    expect(search_page.page.get_by_text("2025.2")).not_to_be_visible()
    expect(search_page.page.get_by_text("2025.1")).not_to_be_visible()
