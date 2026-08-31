from playwright.sync_api import Page, expect

from sa.tests.factories import EvenementAnimalFactory
from sa.tests.pages import EvenementAnimalDetailsPage


def test_evenement_animal_details_page_header(live_server, page: Page):
    evenement = EvenementAnimalFactory()

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    assert details_page.title.text_content() == f"Événement {evenement.numero}"
    assert details_page.etat_badge.text_content() == evenement.get_etat_display()
    assert details_page.statut_evenement_badge.text_content() == evenement.get_statut_evenement_display()


def test_evenement_animal_details_page_informations_generales_block(live_server, page: Page):
    evenement = EvenementAnimalFactory()

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    block = details_page.block("Informations générales")
    expect(block.get_by_text(evenement.maladie.name, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.espece.name, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.get_statut_animal_display(), exact=True)).to_be_visible()


def test_evenement_animal_details_page_informations_block(live_server, page: Page):
    evenement = EvenementAnimalFactory()

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    block = details_page.block("Informations")
    expect(block.get_by_text(evenement.date_creation.strftime("%d/%m/%Y"), exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.get_statut_evenement_display(), exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.date_statut_changed.strftime("%d/%m/%Y"), exact=True)).to_be_visible()


def test_evenement_animal_details_page_detenteur_etablissement_block(live_server, page: Page):
    evenement = EvenementAnimalFactory()

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    block = details_page.block("Détenteur : Établissement")
    expect(block.get_by_text(evenement.numero_identifiant_etablissement, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.autre_identifiant_etablissement, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.siret_etablissement, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.raison_sociale_etablissement, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.adresse_lieu_dit_etablissement, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.commune_etablissement, exact=True)).to_be_visible()
    expect(block.get_by_text(str(evenement.departement_etablissement), exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.code_insee_etablissement, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.get_pays_etablissement_display(), exact=True)).to_be_visible()


def test_evenement_animal_details_page_detenteur_particulier_block(live_server, page: Page):
    evenement = EvenementAnimalFactory(particulier=True)

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    block = details_page.block("Détenteur : Particulier")
    expect(block.get_by_text(evenement.nom_particulier, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.prenom_particulier, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.adresse_particulier, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.commune_particulier, exact=True)).to_be_visible()
    expect(block.get_by_text(str(evenement.departement_particulier), exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.code_insee_particulier, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.email_particulier, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.telephone_particulier, exact=True)).to_be_visible()


def test_evenement_animal_details_page_localisation_block(live_server, page: Page):
    evenement = EvenementAnimalFactory()

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    block = details_page.block("Localisation")
    expect(block.get_by_text(evenement.adresse_lieu_dit, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.commune, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.code_insee, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.numero_identifiant, exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.get_type_lieu_display(), exact=True)).to_be_visible()
    expect(block.get_by_text("Latitude", exact=True)).to_be_visible()
    expect(block.get_by_text("Longitude", exact=True)).to_be_visible()
    expect(page.locator('[data-controller="map-viewer"]')).to_be_visible()


def test_evenement_animal_details_page_with_missing_information(live_server, page: Page):
    evenement = EvenementAnimalFactory(numero_identifiant="", adresse_lieu_dit="")

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    block = details_page.block("Localisation")
    expect(block.get_by_text("Vide").first).to_be_visible()


def test_evenement_animal_details_page_mesures_block(live_server, page: Page):
    evenement = EvenementAnimalFactory(maladie__needs_arrete=True)

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    block = details_page.block("Mesures de gestion")
    expect(block.get_by_text(evenement.date_apms.strftime("%d/%m/%Y"), exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.date_apdi.strftime("%d/%m/%Y"), exact=True)).to_be_visible()
    expect(block.get_by_text(evenement.date_levee.strftime("%d/%m/%Y"), exact=True)).to_be_visible()
