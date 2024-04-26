import pytest
from playwright.sync_api import Page, expect
from ..models import (
    FicheDetection,
    Unite,
    StatutEvenement,
    StatutReglementaire,
    Contexte,
    Administration,
    OrganismeNuisible,
    NumeroFiche,
)


@pytest.fixture(autouse=True)
def setup_data():
    data = {}
    data["unite_mus"] = Unite.objects.create(nom="MUS", type=Administration.objects.create(nom="AC"))
    data["statut_evenement_enqu"] = StatutEvenement.objects.create(libelle="ENQU")
    data["organisme_nuisible_xf"] = OrganismeNuisible.objects.create(libelle_court="Xylella fastidiosa", code_oepp="Xf")
    data["statut_reglementaire_ornq"] = StatutReglementaire.objects.create(code="ORNQ")
    data["contexte_is"] = Contexte.objects.create(nom="informations scientifiques")

    data["fiche_detection"] = FicheDetection.objects.create(
        numero=NumeroFiche.get_next_numero(),
        createur=data["unite_mus"],
        numero_europhyt="1234",
        numero_rasff="54321",
        statut_evenement=data["statut_evenement_enqu"],
        organisme_nuisible=data["organisme_nuisible_xf"],
        statut_reglementaire=data["statut_reglementaire_ornq"],
        contexte=data["contexte_is"],
        date_premier_signalement="2021-01-01",
        commentaire="un commentaire",
        mesures_conservatoires_immediates="des mesures conservatoires immediates",
        mesures_consignation="des mesures de consignation",
        mesures_phytosanitaires="des mesures phytosanitaires",
        mesures_surveillance_specifique="des mesures de surveillance specifique",
    )
    data["edit_fiche_detection_url"] = f"/sv/fiches-detection/{data['fiche_detection'].id}/modification/"
    return data


def test_url(setup_data, live_server, page: Page):
    response = page.request.get(f"{live_server.url}{setup_data['edit_fiche_detection_url']}")
    expect(response).to_be_ok()


def test_page_title(setup_data, live_server, page: Page):
    """Test que le titre de la page est bien "Modification de la fiche détection n°2024.1"""
    page.goto(f"{live_server.url}{setup_data['edit_fiche_detection_url']}")
    expect(page.locator("#fiche-detection-form-header")).to_contain_text("Modification de la fiche détection n°2024.1")


def test_fiche_detection_update_page_content(setup_data, live_server, page: Page):
    """Test que toutes les données de la fiche de détection sont affichées sur la page de modification de la fiche de détection."""
    page.goto(f"{live_server.url}{setup_data['edit_fiche_detection_url']}")

    expect(page.locator("#createur-input")).to_contain_text(setup_data["fiche_detection"].createur.nom)
    expect(page.get_by_label("Statut évènement")).to_contain_text(
        setup_data["fiche_detection"].statut_evenement.libelle
    )
    expect(page.locator("#organisme-nuisible")).to_contain_text(
        setup_data["fiche_detection"].organisme_nuisible.libelle_court
    )
    expect(page.get_by_label("Statut règlementaire")).to_contain_text(
        setup_data["fiche_detection"].statut_reglementaire.libelle
    )
    expect(page.get_by_label("Contexte")).to_contain_text(setup_data["fiche_detection"].contexte.nom)
    expect(page.get_by_label("Date 1er signalement")).to_have_value(
        setup_data["fiche_detection"].date_premier_signalement
    )
    expect(page.get_by_label("Commentaire")).to_have_value(setup_data["fiche_detection"].commentaire)
    expect(page.get_by_label("Mesures conservatoires immédiates")).to_have_value(
        setup_data["fiche_detection"].mesures_conservatoires_immediates
    )
    expect(page.get_by_label("Mesures de consignation")).to_have_value(
        setup_data["fiche_detection"].mesures_consignation
    )
    expect(page.get_by_label("Mesures phytosanitaires")).to_have_value(
        setup_data["fiche_detection"].mesures_phytosanitaires
    )
    expect(page.get_by_label("Mesures de surveillance spécifique")).to_have_value(
        setup_data["fiche_detection"].mesures_surveillance_specifique
    )


def test_fiche_detection_update_with_createur_only(setup_data, live_server, page: Page):
    """Test que la page de modification de la fiche de détection affiche uniquement le créateur pour une fiche détection contenant uniquement le créateur."""
    fiche_detection = FicheDetection.objects.create(
        numero=NumeroFiche.get_next_numero(),
        createur=Unite.objects.create(
            nom="Mission des urgences sanitaires",
            type=Administration.objects.create(nom="AC"),
        ),
    )
    fiche_detection.save()
    edit_fiche_detection_url = f"{live_server.url}/sv/fiches-detection/{fiche_detection.id}/modification/"

    page.goto(edit_fiche_detection_url)

    expect(page.locator("#createur-input")).to_contain_text(fiche_detection.createur.nom)
    expect(page.get_by_label("Statut évènement")).to_contain_text("----")
    expect(page.locator("#organisme-nuisible")).to_contain_text("----")
    expect(page.get_by_label("Statut règlementaire")).to_contain_text("----")
    expect(page.get_by_label("Contexte")).to_contain_text("----")
    expect(page.get_by_label("Date 1er signalement")).to_have_value("")
    expect(page.get_by_label("Commentaire")).to_have_value("")
    expect(page.get_by_label("Mesures conservatoires immédiates")).to_have_value("")
    expect(page.get_by_label("Mesures de consignation")).to_have_value("")
    expect(page.get_by_label("Mesures phytosanitaires")).to_have_value("")
    expect(page.get_by_label("Mesures de surveillance spécifique")).to_have_value("")


def test_fiche_detection_update_without_lieux_and_prelevement(setup_data, live_server, page: Page):
    """Test que les modifications des informations, objet de l'évènement et mesures de gestion sont bien enregistrées apès modification."""
    new_unite = Unite.objects.create(nom="BSV", type=Administration.objects.create(nom="AC"))
    new_statut_evenement = StatutEvenement.objects.create(libelle="TERR")
    # new_organisme_nuisible = OrganismeNuisible.objects.create(code_oepp="un ON", libelle_court="UON")
    new_statut_reglementaire = StatutReglementaire.objects.create(code="AZER")
    new_contexte = Contexte.objects.create(nom="alerte européenne")
    new_date_premier_signalement = "2024-04-25"
    new_commentaire = "nouveau commentaire"
    new_mesures_conservatoires_immediates = "nouvelles mesures conservatoires immediates"
    new_mesures_consignation = "nouvelles mesures de consignation"
    new_mesures_phytosanitaires = "nouvelles mesures phytosanitaires"
    new_mesures_surveillance_specifique = "nouvelles mesures de surveillance specifique"

    page.goto(f"{live_server.url}{setup_data['edit_fiche_detection_url']}")

    page.locator("#createur-input").select_option(str(new_unite.id))
    page.get_by_label("Statut évènement").select_option(str(new_statut_evenement.id))
    # page.locator("#organisme-nuisible-input").select_option(str(new_organisme_nuisible.id))
    # page.locator("#organisme-nuisible").get_by_text("----").nth(1).click()
    # page.get_by_role("option", name=str(new_organisme_nuisible)).click()
    page.get_by_label("Statut règlementaire").select_option(str(new_statut_reglementaire.id))
    page.get_by_label("Contexte").select_option(str(new_contexte.id))
    page.get_by_label("Date 1er signalement").fill(new_date_premier_signalement)
    page.get_by_label("Commentaire").fill(new_commentaire)
    page.get_by_label("Mesures conservatoires immédiates").fill(new_mesures_conservatoires_immediates)
    page.get_by_label("Mesures de consignation").fill(new_mesures_consignation)
    page.get_by_label("Mesures phytosanitaires").fill(new_mesures_phytosanitaires)
    page.get_by_label("Mesures de surveillance spécifique").fill(new_mesures_surveillance_specifique)
    page.click("text=Enregistrer")

    page.wait_for_timeout(200)

    fiche_detection = FicheDetection.objects.get(id=setup_data["fiche_detection"].id)
    assert fiche_detection.createur == new_unite
    assert fiche_detection.statut_evenement == new_statut_evenement
    # assert fiche_detection.organisme_nuisible == new_organisme_nuisible
    assert fiche_detection.statut_reglementaire == new_statut_reglementaire
    assert fiche_detection.contexte == new_contexte
    assert fiche_detection.commentaire == new_commentaire
    assert fiche_detection.mesures_conservatoires_immediates == new_mesures_conservatoires_immediates
    assert fiche_detection.mesures_consignation == new_mesures_consignation
    assert fiche_detection.mesures_phytosanitaires == new_mesures_phytosanitaires
    assert fiche_detection.mesures_surveillance_specifique == new_mesures_surveillance_specifique


def test_add_new_lieu(setup_data, live_server, page: Page):
    page.goto(f"{live_server.url}{setup_data['edit_fiche_detection_url']}")
    page.get_by_role("button", name="Ajouter une localisation").click()
    page.get_by_label("Nom de la localisation").click()
    page.get_by_label("Nom de la localisation").fill("test")
    page.get_by_label("Ajouter une localisation").get_by_role("button", name="Enregistrer").click()
    page.get_by_role("button", name="Enregistrer").click()

    page.wait_for_timeout(200)

    fiche_detection = FicheDetection.objects.get(id=setup_data["fiche_detection"].id)
    assert fiche_detection.lieux.count() == 1
    assert fiche_detection.lieux.first().nom == "test"
