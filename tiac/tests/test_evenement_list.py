from playwright.sync_api import Page, expect

from core.factories import ContactStructureFactory, ContactAgentFactory
from tiac.factories import EvenementSimpleFactory, InvestigationTiacFactory, EtablissementFactory
from tiac.models import EvenementSimple, InvestigationTiac, TypeEvenement
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
    assert search_page.etablissement_cell().text_content() == f"{etablissement.raison_sociale} {etablissement.commune}"
    assert search_page.malades_cell().text_content() == str(evenement.nb_sick_persons)
    assert search_page.type_cell().text_content() == f"Enr. simple / {evenement.get_follow_up_display()}"
    assert search_page.conclusion_cell().text_content() == "-"
    assert search_page.danger_cell().text_content() == "-"
    assert search_page.etat_cell().text_content() == "Brouillon"


def test_row_content_investigation_tiac(live_server, mocked_authentification_user, page: Page):
    evenement: InvestigationTiac = InvestigationTiacFactory(type_evenement=TypeEvenement.INVESTIGATION_COORDONNEE)
    etablissement = EtablissementFactory(evenement_simple=None, investigation_tiac=evenement)
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    assert search_page.numero_cell().text_content() == evenement.numero
    assert search_page.createur_cell().text_content() == mocked_authentification_user.agent.structure.libelle
    assert search_page.date_reception_cell().text_content() == evenement.date_reception.strftime("%d/%m/%Y")
    assert search_page.etablissement_cell().text_content() == f"{etablissement.raison_sociale} {etablissement.commune}"
    assert search_page.malades_cell().text_content() == str(evenement.nb_sick_persons)
    assert search_page.type_cell().text_content() == "Invest. coord. / MUS informée"
    assert search_page.conclusion_cell().text_content() == "-"
    assert search_page.danger_cell().text_content() == "-"
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
    evenement_1 = EvenementSimpleFactory()
    evenement_2 = InvestigationTiacFactory()
    evenement_3 = EvenementSimpleFactory()
    evenement_4 = InvestigationTiacFactory()
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
