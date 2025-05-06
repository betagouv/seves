from playwright.sync_api import Page, expect

from core.factories import StructureFactory
from core.models import LienLibre
from ssa.factories import EvenementProduitFactory
from ssa.models import TypeEvenement, EvenementProduit
from ssa.tests.pages import EvenementProduitListPage


def test_list_table_order(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(numero_annee=2025, numero_evenement=2)
    EvenementProduitFactory(numero_annee=2025, numero_evenement=1)
    EvenementProduitFactory(numero_annee=2025, numero_evenement=22)
    EvenementProduitFactory(numero_annee=2024, numero_evenement=22)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    assert search_page.numero_cell(line_index=1).text_content() == "2025.22"
    assert search_page.numero_cell(line_index=2).text_content() == "2025.2"
    assert search_page.numero_cell(line_index=3).text_content() == "2025.1"
    assert search_page.numero_cell(line_index=4).text_content() == "2024.22"


def test_list_filtered_by_visibilite(live_server, mocked_authentification_user, page: Page):
    evenement_1 = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON, createur=StructureFactory())
    evenement_2 = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS, createur=StructureFactory())
    evenement_3 = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON)
    evenement_4 = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    expect(page.get_by_text(evenement_1.numero)).not_to_be_visible()
    expect(page.get_by_text(evenement_2.numero)).to_be_visible()
    expect(page.get_by_text(evenement_3.numero)).to_be_visible()
    expect(page.get_by_text(evenement_4.numero)).to_be_visible()


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
    assert search_page.description_cell().text_content() == evenement.product_description
    assert search_page.createur_cell().text_content() == mocked_authentification_user.agent.structure.libelle
    assert search_page.etat_cell().text_content() == "Brouillon"
    assert search_page.liens_cell().text_content() == "2"


def test_list_can_filter_by_numero(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(numero_annee=2025, numero_evenement=2)
    EvenementProduitFactory(numero_annee=2025, numero_evenement=1)
    EvenementProduitFactory(numero_annee=2024, numero_evenement=22)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.numero_field.fill("2025")
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "2025.2"
    expect(search_page.page.get_by_text("2024.22")).not_to_be_visible()


def test_list_can_filter_by_numero_rasff(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(numero_rasff=123456, numero_annee=2025, numero_evenement=2)
    EvenementProduitFactory(numero_rasff=987654, numero_annee=2025, numero_evenement=1)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.numero_rasff_field.fill("123456")
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "2025.2"
    expect(search_page.page.get_by_text("2025.1")).not_to_be_visible()


def test_list_can_filter_by_type_evenement(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(type_evenement=TypeEvenement.ALERTE_PRODUIT_UE, numero_annee=2025, numero_evenement=2)
    EvenementProduitFactory(type_evenement=TypeEvenement.NON_ALERTE, numero_annee=2025, numero_evenement=1)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.type_evenement_select.select_option(TypeEvenement.NON_ALERTE)
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "2025.1"
    expect(search_page.page.get_by_text("2025.2")).not_to_be_visible()


def test_list_can_filter_by_date(live_server, mocked_authentification_user, page: Page):
    EvenementProduitFactory(date_creation="2024-06-18", numero_annee=2025, numero_evenement=3)
    EvenementProduitFactory(date_creation="2024-06-19", numero_annee=2025, numero_evenement=2)
    EvenementProduitFactory(date_creation="2024-06-22", numero_annee=2025, numero_evenement=1)

    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.start_date_field.fill("2024-06-19")
    search_page.end_date_field.fill("2024-06-20")
    search_page.submit_search()
    assert search_page.numero_cell().text_content() == "2025.2"
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
