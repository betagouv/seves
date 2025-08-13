from playwright.sync_api import Page

from tiac.factories import EvenementSimpleFactory
from tiac.models import EvenementSimple
from tiac.tests.pages import EvenementListPage


def test_list_table_order(live_server, mocked_authentification_user, page: Page):
    EvenementSimpleFactory(numero_annee=2025, numero_evenement=2)
    EvenementSimpleFactory(numero_annee=2025, numero_evenement=1)
    EvenementSimpleFactory(numero_annee=2025, numero_evenement=22)
    EvenementSimpleFactory(numero_annee=2024, numero_evenement=22)
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    assert search_page.numero_cell(line_index=1).text_content() == "T-2025.22"
    assert search_page.numero_cell(line_index=2).text_content() == "T-2025.2"
    assert search_page.numero_cell(line_index=3).text_content() == "T-2025.1"
    assert search_page.numero_cell(line_index=4).text_content() == "T-2024.22"


def test_row_content(live_server, mocked_authentification_user, page: Page):
    evenement: EvenementSimple = EvenementSimpleFactory()
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    assert search_page.numero_cell().text_content() == evenement.numero
    assert search_page.createur_cell().text_content() == mocked_authentification_user.agent.structure.libelle
    assert search_page.date_reception_cell().text_content() == evenement.date_reception.strftime("%d/%m/%Y")
    assert search_page.etablissement_cell().text_content() == "-"
    assert search_page.malades_cell().text_content() == str(evenement.nb_sick_persons)
    assert search_page.type_cell().text_content() == f"Enr. simple / {evenement.get_follow_up_display()}"
    assert search_page.conclusion_cell().text_content() == "-"
    assert search_page.danger_cell().text_content() == "-"
    assert search_page.etat_cell().text_content() == "Brouillon"
