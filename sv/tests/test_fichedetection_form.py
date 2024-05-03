import json
import pytest
from playwright.sync_api import Page, expect
from django.urls import reverse
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements
from .conftest import check_select_options
from ..models import (
    Departement,
)


@pytest.fixture(autouse=True)
def test_goto_fiche_detection_creation_url(live_server, page: Page):
    """Ouvre la page de création d'une fiche de détection"""
    add_fiche_detection_form_url = reverse("fiche-detection-creation")
    return page.goto(f"{live_server.url}{add_fiche_detection_form_url}")


def _add_new_localisation(
    page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("nom localisation")
    lieu_form_elements.adresse_input.click()
    lieu_form_elements.adresse_input.fill("une adresse")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("une commune")
    lieu_form_elements.code_insee_input.click()
    lieu_form_elements.code_insee_input.fill("17000")
    lieu_form_elements.departement_input.select_option("62")
    lieu_form_elements.coord_gps_lamber93_latitude_input.click()
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000000")
    lieu_form_elements.coord_gps_lamber93_longitude_input.click()
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200000")
    lieu_form_elements.coord_gps_wgs84_latitude_input.click()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("1")
    lieu_form_elements.coord_gps_wgs84_longitude_input.click()
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("2")
    lieu_form_elements.save_btn.click()


def _check_add_localisation_form_fields_are_empty(page: Page, lieu_form_elements: LieuFormDomElements):
    """Vérifie que le formulaire d'ajout d'une localisation est vide"""
    expect(lieu_form_elements.nom_input).to_be_empty()
    expect(lieu_form_elements.adresse_input).to_be_empty()
    expect(lieu_form_elements.commune_input).to_be_empty()
    expect(lieu_form_elements.code_insee_input).to_be_empty()
    expect(lieu_form_elements.departement_input).to_contain_text("----")
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_be_empty()


# =============
# Partie Informations, Objet de l'évènement, Mesures de gestion
# =============
def test_date_creation_field_is_disabled(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que le champ Date de création est désactivé"""
    expect(form_elements.date_creation_input).to_be_disabled()


def test_createur_field_is_required(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que le champ Créateur est requis pour la création d'une fiche de détection"""
    expect(form_elements.createur_input).to_have_attribute("required", "")


# =============
# Partie Lieux
# =============

# Ajouter un lieu


def test_add_localisation_button(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que le bouton Ajouter une localisation affiche le formulaire d’ajout d’une nouvelle localisation dans la modal"""
    form_elements.add_lieu_btn.click()
    expect(page.get_by_role("dialog")).to_be_visible()


def test_close_button_of_add_lieu_form_modal(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que le bouton Fermer ferme la modal d'ajout d'une localisation"""
    form_elements.add_lieu_btn.click()
    page.get_by_role("button", name="Fermer").click()
    expect(page.get_by_role("dialog")).to_be_hidden()


def test_cancel_button_of_add_lieu_form_modal(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que le bouton Annuler ferme la modal d'ajout d'une localisation"""
    form_elements.add_lieu_btn.click()
    page.get_by_role("button", name="Annuler").click()
    expect(page.get_by_role("dialog")).to_be_hidden()


def test_add_localisation_form_have_all_fields(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le formulaire d'ajout d'une localisation contient bien les champs attendus."""
    form_elements.add_lieu_btn.click()

    expect(lieu_form_elements.close_btn).to_be_visible()
    expect(lieu_form_elements.close_btn).to_have_text("Fermer")

    expect(lieu_form_elements.title).to_be_visible()
    expect(lieu_form_elements.title).to_have_text("Ajouter une localisation")

    expect(lieu_form_elements.nom_label).to_be_visible()
    expect(lieu_form_elements.nom_label).to_have_text("Nom de la localisation")
    expect(lieu_form_elements.nom_input).to_be_visible()
    expect(lieu_form_elements.nom_input).to_be_empty()

    expect(lieu_form_elements.adresse_label).to_be_visible()
    expect(lieu_form_elements.adresse_label).to_have_text("Adresse ou lieu-dit")
    expect(lieu_form_elements.adresse_input).to_be_empty()

    expect(lieu_form_elements.commune_label).to_be_visible()
    expect(lieu_form_elements.commune_label).to_have_text("Commune")
    expect(lieu_form_elements.commune_input).to_be_empty()

    expect(lieu_form_elements.code_insee_label).to_be_visible()
    expect(lieu_form_elements.code_insee_label).to_have_text("Code INSEE")
    expect(lieu_form_elements.code_insee_input).to_be_empty()

    expect(lieu_form_elements.departement_label).to_be_visible()
    expect(lieu_form_elements.departement_label).to_have_text("Département")
    departements = list(Departement.objects.values_list("nom", flat=True))
    check_select_options(page, "Département", departements)

    expect(lieu_form_elements.coord_gps_lamber93_latitude_label).to_be_visible()
    expect(lieu_form_elements.coord_gps_lamber93_latitude_label).to_have_text("Coordonnées GPS (Lambert 93)")
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_have_attribute("placeholder", "Latitude")
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_have_attribute("placeholder", "Longitude")

    expect(lieu_form_elements.coord_gps_wgs84_latitude_label).to_be_visible()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_label).to_have_text("Coordonnées GPS (WGS84)")
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_have_attribute("placeholder", "Latitude")
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_have_attribute("placeholder", "Longitude")

    expect(lieu_form_elements.cancel_btn).to_be_visible()
    expect(lieu_form_elements.cancel_btn).to_have_text("Annuler")

    expect(lieu_form_elements.save_btn).to_be_visible()
    expect(lieu_form_elements.save_btn).to_have_text("Enregistrer")


def test_nom_localisation_is_required_in_add_lieu_form(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le champ Nom de la localisation est requis pour l'ajout d'une localisation"""
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.nom_input).to_have_attribute("required", "")


def test_code_insee_is_numeric_in_add_lieu_form(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le champ Code INSEE est un champ numérique"""
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.code_insee_input).to_have_attribute("type", "number")


def test_code_insee_min_max_value_in_add_lieu_form(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le champ Code INSEE a une valeur minimale de 1001 et maximale de 99999"""
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.code_insee_input).to_have_attribute("min", "1001")
    expect(lieu_form_elements.code_insee_input).to_have_attribute("max", "99999")


def test_coordonnees_gps_are_numeric_in_add_lieu_form(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que les champs de coordonnées GPS (Lambert 93 et WGS84) sont des champs numériques"""
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_have_attribute("type", "number")
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_have_attribute("type", "number")
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_have_attribute("type", "number")
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_have_attribute("type", "number")


def test_latitude_min_max_value_of_lambert93_format_in_add_lieu_form(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que la valeur minimal de la latitude du format lambert 93 est de 6000000 et la valeur max est de 7200000"""
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_have_attribute("min", "6000000")
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_have_attribute("max", "7200000")


def test_longitude_min_max_value_of_lambert93_format_in_add_lieu_form(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que la valeur minimal de la longitude du format lambert 93 est de 200000 et la valeur max est de 1200000"""
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_have_attribute("min", "200000")
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_have_attribute("max", "1200000")


def test_add_lieu_to_list(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le lieu ajouté est bien visible dans la liste des localisations"""
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test localisation")
    lieu_form_elements.save_btn.click()
    expect(page.locator("#localisations").get_by_text("test localisation")).to_be_visible()
    elements = page.query_selector_all(".localisation-initiale")
    assert len(elements) == 1


def test_added_lieu_content_in_list(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le contenu du lieu ajouté contient le nom de la localisation, la commune et les boutons de suppression et de modification"""
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test localisation")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("test commune")
    lieu_form_elements.save_btn.click()
    expect(page.locator("#localisations").get_by_text("test localisation")).to_be_visible()
    expect(page.locator("#localisations")).to_contain_text("test localisation")
    expect(page.get_by_text("test commune")).to_be_visible()
    expect(page.locator("#localisations")).to_contain_text("test commune")
    expect(page.get_by_role("button", name="Modifier la localisation")).to_be_visible()
    expect(page.get_by_role("button", name="Supprimer la localisation")).to_be_visible()


@pytest.mark.django_db(serialized_rollback=True)
def test_lieu_is_added_to_alpinejs_data(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le lieu ajouté est bien ajouté dans le tableau de données alpinejs"""
    form_elements.add_lieu_btn.click()

    # ajout d'un lieu via le formulaire
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("nom localisation")
    lieu_form_elements.adresse_input.click()
    lieu_form_elements.adresse_input.fill("une adresse")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("une commune")
    lieu_form_elements.code_insee_input.click()
    lieu_form_elements.code_insee_input.fill("17000")
    lieu_form_elements.departement_input.select_option("62")
    lieu_form_elements.coord_gps_lamber93_latitude_input.click()
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000000")
    lieu_form_elements.coord_gps_lamber93_longitude_input.click()
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200000")
    lieu_form_elements.coord_gps_wgs84_latitude_input.click()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("1")
    lieu_form_elements.coord_gps_wgs84_longitude_input.click()
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("2")
    lieu_form_elements.save_btn.click()

    localisations_json = page.get_by_test_id("localisations").input_value()
    localisations = json.loads(localisations_json)
    assert len(localisations) == 1
    assert localisations[0]["nomLocalisation"] == "nom localisation"
    assert localisations[0]["adresseLieuDit"] == "une adresse"
    assert localisations[0]["commune"] == "une commune"
    assert localisations[0]["codeINSEE"] == "17000"
    assert localisations[0]["departementId"] == "62"
    assert localisations[0]["coordGPSLambert93Latitude"] == "6000000"
    assert localisations[0]["coordGPSLambert93Longitude"] == "200000"
    assert localisations[0]["coordGPSWGS84Latitude"] == "1"
    assert localisations[0]["coordGPSWGS84Longitude"] == "2"


@pytest.mark.django_db(serialized_rollback=True)
def test_add_two_lieux_to_list(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que les lieux ajoutés sont bien visibles dans la liste des localisations"""
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test localisation")
    lieu_form_elements.save_btn.click()

    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test localisation 2")
    lieu_form_elements.save_btn.click()

    expect(page.locator("#localisations").get_by_text("test localisation", exact=True)).to_be_visible()
    expect(page.locator("#localisations").get_by_text("test localisation 2", exact=True)).to_be_visible()
    expect(page.locator("#localisations")).to_contain_text("a")
    expect(page.locator("#localisations")).to_contain_text("b")
    elements = page.query_selector_all(".localisation-initiale")
    assert len(elements) == 2


@pytest.mark.django_db(serialized_rollback=True)
def test_two_lieux_are_added_to_alpinejs_data(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que les lieux ajoutés sont bien ajoutés dans le tableau de données alpinejs"""
    # ajout du premier lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("nom localisation")
    lieu_form_elements.adresse_input.click()
    lieu_form_elements.adresse_input.fill("une adresse")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("une commune")
    lieu_form_elements.code_insee_input.click()
    lieu_form_elements.code_insee_input.fill("17000")
    lieu_form_elements.departement_input.select_option("62")
    lieu_form_elements.coord_gps_lamber93_latitude_input.click()
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000000")
    lieu_form_elements.coord_gps_lamber93_longitude_input.click()
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200000")
    lieu_form_elements.coord_gps_wgs84_latitude_input.click()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("1")
    lieu_form_elements.coord_gps_wgs84_longitude_input.click()
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("2")
    lieu_form_elements.save_btn.click()

    # ajout du deuxième lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("nom localisation 2")
    lieu_form_elements.adresse_input.click()
    lieu_form_elements.adresse_input.fill("une adresse 2")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("une commune 2")
    lieu_form_elements.code_insee_input.click()
    lieu_form_elements.code_insee_input.fill("17440")
    lieu_form_elements.departement_input.select_option("62")
    lieu_form_elements.coord_gps_lamber93_latitude_input.click()
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000000")
    lieu_form_elements.coord_gps_lamber93_longitude_input.click()
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200000")
    lieu_form_elements.coord_gps_wgs84_latitude_input.click()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("1")
    lieu_form_elements.coord_gps_wgs84_longitude_input.click()
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("2")
    lieu_form_elements.save_btn.click()

    localisations_json = page.get_by_test_id("localisations").input_value()
    localisations = json.loads(localisations_json)
    assert len(localisations) == 2
    assert localisations[0]["nomLocalisation"] == "nom localisation"
    assert localisations[0]["adresseLieuDit"] == "une adresse"
    assert localisations[0]["commune"] == "une commune"
    assert localisations[0]["codeINSEE"] == "17000"
    assert localisations[0]["departementId"] == "62"
    assert localisations[0]["coordGPSLambert93Latitude"] == "6000000"
    assert localisations[0]["coordGPSLambert93Longitude"] == "200000"
    assert localisations[0]["coordGPSWGS84Latitude"] == "1"
    assert localisations[0]["coordGPSWGS84Longitude"] == "2"
    assert localisations[1]["nomLocalisation"] == "nom localisation 2"
    assert localisations[1]["adresseLieuDit"] == "une adresse 2"
    assert localisations[1]["commune"] == "une commune 2"
    assert localisations[1]["codeINSEE"] == "17440"
    assert localisations[1]["departementId"] == "62"
    assert localisations[1]["coordGPSLambert93Latitude"] == "6000000"
    assert localisations[1]["coordGPSLambert93Longitude"] == "200000"
    assert localisations[1]["coordGPSWGS84Latitude"] == "1"
    assert localisations[1]["coordGPSWGS84Longitude"] == "2"


# Modifier un lieu


def test_edit_lieu_button_show_form_in_modal(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le bouton Modifier la localisation affiche le formulaire de modification dans une modal"""
    # ajout d'un lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test localisation")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("test commune")
    lieu_form_elements.save_btn.click()

    page.get_by_role("button", name="Modifier la localisation").click()

    expect(page.get_by_role("dialog")).to_be_visible()


def test_edit_lieu_modal_title_and_actions_btn(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le titre de la modal de modification d'une localisation est bien 'Modifier la localisation'"""
    # ajout d'un lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test localisation")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("test commune")
    lieu_form_elements.save_btn.click()

    page.get_by_role("button", name="Modifier la localisation").click()

    expect(page.get_by_role("heading", name="Modifier la localisation")).to_be_visible()
    expect(page.locator("#modal-add-edit-localisation-title")).to_have_text("Modifier la localisation")
    expect(page.get_by_label("Modifier la localisation").locator('input[type="submit"]')).to_have_text(
        "Enregistrer les modifications"
    )


def test_edit_lieu_form_with_only_nom_localisation(
    live_server, page: Page, lieu_form_elements: LieuFormDomElements, form_elements: FicheDetectionFormDomElements
):
    """Lors de la modification d'une localisation contenant seulement le nom, seulement le champ nom de la localisation est pré-rempli, les autres champs sont vides."""
    # ajout d'un lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test localisation")
    lieu_form_elements.save_btn.click()

    page.get_by_role("button", name="Modifier la localisation").click()

    expect(lieu_form_elements.nom_input).to_have_value("test localisation")
    expect(lieu_form_elements.adresse_input).to_be_empty()
    expect(lieu_form_elements.commune_input).to_be_empty()
    expect(lieu_form_elements.code_insee_input).to_be_empty()
    expect(lieu_form_elements.departement_input).to_contain_text("----")
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_be_empty()


@pytest.mark.django_db(serialized_rollback=True)
def test_edit_lieu_form_have_all_fields(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le formulaire de modification d'une localisation contient bien les champs attendus et que ceux-ci sont pré-remplis avec les valeurs du lieu à modifier."""
    # création d'un lieu TODO: FACTORISER
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("un nom de localisation")
    lieu_form_elements.adresse_input.click()
    lieu_form_elements.adresse_input.fill("une adresse")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("une commune")
    lieu_form_elements.code_insee_input.click()
    lieu_form_elements.code_insee_input.fill("17000")
    lieu_form_elements.departement_input.select_option("62")
    lieu_form_elements.coord_gps_lamber93_latitude_input.click()
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000000")
    lieu_form_elements.coord_gps_lamber93_longitude_input.click()
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200000")
    lieu_form_elements.coord_gps_wgs84_latitude_input.click()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("8")
    lieu_form_elements.coord_gps_wgs84_longitude_input.click()
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("9")
    lieu_form_elements.save_btn.click()

    # modification du lieu
    page.get_by_role("button", name="Modifier la localisation").click()

    expect(lieu_form_elements.close_btn).to_be_visible()
    expect(lieu_form_elements.close_btn).to_have_text("Fermer")

    expect(page.get_by_role("heading", name="Modifier la localisation")).to_be_visible()
    expect(page.locator("#modal-add-edit-localisation-title")).to_have_text("Modifier la localisation")

    expect(lieu_form_elements.nom_label).to_be_visible()
    expect(lieu_form_elements.nom_label).to_have_text("Nom de la localisation")
    expect(lieu_form_elements.nom_input).to_be_visible()
    expect(lieu_form_elements.nom_input).to_have_value("un nom de localisation")

    expect(lieu_form_elements.adresse_label).to_be_visible()
    expect(lieu_form_elements.adresse_label).to_have_text("Adresse ou lieu-dit")
    expect(lieu_form_elements.adresse_input).to_be_visible()
    expect(lieu_form_elements.adresse_input).to_have_value("une adresse")

    expect(lieu_form_elements.commune_label).to_be_visible()
    expect(lieu_form_elements.commune_label).to_have_text("Commune")
    expect(lieu_form_elements.commune_input).to_be_visible()
    expect(lieu_form_elements.commune_input).to_have_value("une commune")

    expect(lieu_form_elements.code_insee_label).to_be_visible()
    expect(lieu_form_elements.code_insee_label).to_have_text("Code INSEE")
    expect(lieu_form_elements.code_insee_input).to_be_visible()
    expect(lieu_form_elements.code_insee_input).to_have_value("17000")

    expect(lieu_form_elements.departement_label).to_be_visible()
    expect(lieu_form_elements.departement_label).to_have_text("Département")
    expect(lieu_form_elements.departement_input).to_be_visible()
    expect(lieu_form_elements.departement_input).to_contain_text("Charente-Maritime (17)")
    expect(lieu_form_elements.departement_input).to_contain_text("62")

    expect(lieu_form_elements.coord_gps_lamber93_latitude_label).to_be_visible()
    expect(lieu_form_elements.coord_gps_lamber93_latitude_label).to_have_text("Coordonnées GPS (Lambert 93)")
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_be_visible()
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_have_value("6000000")
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_be_visible()
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_have_value("200000")

    expect(lieu_form_elements.coord_gps_wgs84_latitude_label).to_be_visible()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_label).to_have_text("Coordonnées GPS (WGS84)")
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_be_visible()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_have_value("8")
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_be_visible()
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_have_value("9")


@pytest.mark.django_db(serialized_rollback=True)
def test_edit_lieu_form_have_all_fields_with_multiple_localisations(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le formulaire de modification d'une localisation contient bien les champs attendus
    et que ceux-ci sont pré-remplis avec les valeurs du lieu à modifier si plusieurs localisations sont présentent dans la liste"""
    # ajout du premier lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("nom localisation")
    lieu_form_elements.adresse_input.click()
    lieu_form_elements.adresse_input.fill("une adresse")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("une commune")
    lieu_form_elements.code_insee_input.click()
    lieu_form_elements.code_insee_input.fill("17000")
    lieu_form_elements.departement_input.select_option("62")
    lieu_form_elements.coord_gps_lamber93_latitude_input.click()
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000000")
    lieu_form_elements.coord_gps_lamber93_longitude_input.click()
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200000")
    lieu_form_elements.coord_gps_wgs84_latitude_input.click()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("1")
    lieu_form_elements.coord_gps_wgs84_longitude_input.click()
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("2")
    lieu_form_elements.save_btn.click()

    # ajout du deuxième lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("nom localisation 2")
    lieu_form_elements.adresse_input.click()
    lieu_form_elements.adresse_input.fill("une adresse 2")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("une commune 2")
    lieu_form_elements.code_insee_input.click()
    lieu_form_elements.code_insee_input.fill("17440")
    lieu_form_elements.departement_input.select_option("62")
    lieu_form_elements.coord_gps_lamber93_latitude_input.click()
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000002")
    lieu_form_elements.coord_gps_lamber93_longitude_input.click()
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200002")
    lieu_form_elements.coord_gps_wgs84_latitude_input.click()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("12")
    lieu_form_elements.coord_gps_wgs84_longitude_input.click()
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("22")
    lieu_form_elements.save_btn.click()

    # vérification des valeurs du premier lieu
    page.get_by_role("button", name="Modifier la localisation").first.click()
    expect(lieu_form_elements.nom_input).to_have_value("nom localisation")
    expect(lieu_form_elements.adresse_input).to_have_value("une adresse")
    expect(lieu_form_elements.commune_input).to_have_value("une commune")
    expect(lieu_form_elements.code_insee_input).to_have_value("17000")
    expect(lieu_form_elements.departement_input).to_have_value("62")
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_have_value("6000000")
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_have_value("200000")
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_have_value("1")
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_have_value("2")
    page.get_by_role("button", name="Fermer").click()

    # vérification des valeurs du deuxième lieu
    page.get_by_role("button", name="Modifier la localisation").nth(1).click()
    expect(lieu_form_elements.nom_input).to_have_value("nom localisation 2")
    expect(lieu_form_elements.adresse_input).to_have_value("une adresse 2")
    expect(lieu_form_elements.commune_input).to_have_value("une commune 2")
    expect(lieu_form_elements.code_insee_input).to_have_value("17440")
    expect(lieu_form_elements.departement_input).to_have_value("62")
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_have_value("6000002")
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_have_value("200002")
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_have_value("12")
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_have_value("22")
    page.get_by_role("button", name="Fermer").click()


@pytest.mark.django_db(serialized_rollback=True)
def test_edit_lieu_is_updated_in_alpinejs_data(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le lieu modifié est bien mis à jour dans le tableau de données alpinejs"""
    # ajout d'un lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("nom localisation")
    lieu_form_elements.adresse_input.click()
    lieu_form_elements.adresse_input.fill("une adresse")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("une commune")
    lieu_form_elements.code_insee_input.click()
    lieu_form_elements.code_insee_input.fill("17000")
    lieu_form_elements.departement_input.select_option("62")
    lieu_form_elements.coord_gps_lamber93_latitude_input.click()
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000000")
    lieu_form_elements.coord_gps_lamber93_longitude_input.click()
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200000")
    lieu_form_elements.coord_gps_wgs84_latitude_input.click()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("1")
    lieu_form_elements.coord_gps_wgs84_longitude_input.click()
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("2")
    lieu_form_elements.save_btn.click()

    # modification du lieu
    page.get_by_role("button", name="Modifier la localisation").click()
    lieu_form_elements.nom_input.fill("nom localisation modifié")
    lieu_form_elements.adresse_input.fill("une adresse modifiée")
    lieu_form_elements.commune_input.fill("une commune modifiée")
    lieu_form_elements.code_insee_input.fill("17001")
    lieu_form_elements.departement_input.select_option("63")
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000001")
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200001")
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("11")
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("21")
    page.get_by_role("button", name="Enregistrer les modifications").click()

    # vérification des valeurs du lieu modifié
    localisations_json = page.get_by_test_id("localisations").input_value()
    localisations = json.loads(localisations_json)
    assert localisations[0]["nomLocalisation"] == "nom localisation modifié"
    assert localisations[0]["adresseLieuDit"] == "une adresse modifiée"
    assert localisations[0]["commune"] == "une commune modifiée"
    assert localisations[0]["codeINSEE"] == "17001"
    assert localisations[0]["departementId"] == "63"
    assert localisations[0]["coordGPSLambert93Latitude"] == "6000001"
    assert localisations[0]["coordGPSLambert93Longitude"] == "200001"
    assert localisations[0]["coordGPSWGS84Latitude"] == "11"
    assert localisations[0]["coordGPSWGS84Longitude"] == "21"


@pytest.mark.django_db(serialized_rollback=True)
def test_add_lieu_form_is_empty_after_edit(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le formulaire d'ajout d'une localisation est vide après la modification d'une localisation"""
    # ajout d'un lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("nom localisation")
    lieu_form_elements.adresse_input.click()
    lieu_form_elements.adresse_input.fill("une adresse")
    lieu_form_elements.commune_input.click()
    lieu_form_elements.commune_input.fill("une commune")
    lieu_form_elements.code_insee_input.click()
    lieu_form_elements.code_insee_input.fill("17000")
    lieu_form_elements.departement_input.select_option("62")
    lieu_form_elements.coord_gps_lamber93_latitude_input.click()
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000000")
    lieu_form_elements.coord_gps_lamber93_longitude_input.click()
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200000")
    lieu_form_elements.coord_gps_wgs84_latitude_input.click()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("1")
    lieu_form_elements.coord_gps_wgs84_longitude_input.click()
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("2")
    lieu_form_elements.save_btn.click()

    # modification du lieu
    page.get_by_role("button", name="Modifier la localisation").click()
    lieu_form_elements.nom_input.fill("nom localisation modifié")
    lieu_form_elements.adresse_input.fill("une adresse modifiée")
    lieu_form_elements.commune_input.fill("une commune modifiée")
    lieu_form_elements.code_insee_input.fill("17001")
    lieu_form_elements.departement_input.select_option("63")
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill("6000001")
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill("200001")
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("11")
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("21")
    page.get_by_role("button", name="Enregistrer les modifications").click()

    # vérification que le formulaire d'ajout d'une localisation est vide
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.nom_input).to_be_empty()
    expect(lieu_form_elements.adresse_input).to_be_empty()
    expect(lieu_form_elements.commune_input).to_be_empty()
    expect(lieu_form_elements.code_insee_input).to_be_empty()
    expect(lieu_form_elements.departement_input).to_contain_text("----")
    expect(lieu_form_elements.coord_gps_lamber93_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_lamber93_longitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_be_empty()


@pytest.mark.django_db(serialized_rollback=True)
def test_add_lieu_form_is_empty_after_close_edit_form_with_close_btn_without_save(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que si je quitte la modification d’une localisation sans enregistrer via le  bouton fermer,
    je dois trouver le formulaire d’ajout d’une localisation vide"""
    _add_new_localisation(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Modifier la localisation").click()
    page.get_by_role("button", name="Fermer").click()
    form_elements.add_lieu_btn.click()

    _check_add_localisation_form_fields_are_empty(page, lieu_form_elements)


@pytest.mark.django_db(serialized_rollback=True)
def test_add_lieu_form_is_empty_after_close_edit_form_with_cancel_btn_without_save(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que si je quitte la modification d’une localisation sans enregistrer via le bouton annuler,
    je dois trouver le formulaire d’ajout d’une localisation vide"""
    _add_new_localisation(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Modifier la localisation").click()
    page.get_by_role("button", name="Annuler").click()
    form_elements.add_lieu_btn.click()

    _check_add_localisation_form_fields_are_empty(page, lieu_form_elements)


@pytest.mark.django_db(serialized_rollback=True)
def test_add_lieu_form_is_empty_after_close_edit_form_with_esc_key_without_save(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que si je quitte la modification d’une localisation sans enregistrer via la touche echap du clavier,
    je dois trouver le formulaire d’ajout d’une localisation vide"""
    _add_new_localisation(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Modifier la localisation").click()
    page.keyboard.press("Escape")
    form_elements.add_lieu_btn.click()

    _check_add_localisation_form_fields_are_empty(page, lieu_form_elements)


@pytest.mark.django_db(serialized_rollback=True)
def test_add_lieu_form_is_empty_after_close_edit_form_with_click_outside_modal_without_save(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que si je quitte la modification d’une localisation sans enregistrer via un clic en dehors de la modal,
    je dois trouver le formulaire d’ajout d’une localisation vide"""
    _add_new_localisation(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Modifier la localisation").click()
    page.mouse.click(0, 0)  # clic en dehors de la modal
    form_elements.add_lieu_btn.click()

    _check_add_localisation_form_fields_are_empty(page, lieu_form_elements)


# Supprimer un lieu


@pytest.mark.django_db(serialized_rollback=True)
def test_delete_lieu_button_show_confirmation_modal(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test qu'une modal de confirmation est affichée lors de la suppression d'une localisation liée à aucun prélèvement"""
    _add_new_localisation(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Supprimer la localisation").click()

    expect(page.get_by_role("dialog")).to_be_visible()


@pytest.mark.django_db(serialized_rollback=True)
def test_delete_lieu_from_list(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que la localisation est bien supprimée de la liste des localisations après confirmation"""
    _add_new_localisation(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Supprimer la localisation").click()
    page.get_by_role("dialog", name="Supprimer").get_by_role("button", name="Supprimer").click()

    expect(page.locator("#localisations")).not_to_contain_text("nom localisation")
    elements = page.query_selector_all(".localisation-initiale")
    assert len(elements) == 0

    localisations_json = page.get_by_test_id("localisations").input_value()
    localisations = json.loads(localisations_json)
    assert len(localisations) == 0


@pytest.mark.django_db(serialized_rollback=True)
def test_delete_lieu_from_list_with_multiple_localisations(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que la localisation est bien supprimée de la liste des localisations après confirmation
    et que c'est la bonne localisation qui est supprimée"""
    # ajout du premier lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("lorem")
    lieu_form_elements.save_btn.click()

    # ajout du deuxième lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("ipsum")
    lieu_form_elements.save_btn.click()

    # suppression du premier lieu
    page.get_by_role("button", name="Supprimer la localisation").first.click()
    page.get_by_role("dialog", name="Supprimer").get_by_role("button", name="Supprimer").click()

    expect(page.locator("#localisations")).not_to_contain_text("lorem")
    expect(page.locator("#localisations")).to_contain_text("ipsum")
    elements = page.query_selector_all(".localisation-initiale")
    assert len(elements) == 1

    localisations_json = page.get_by_test_id("localisations").input_value()
    localisations = json.loads(localisations_json)
    assert len(localisations) == 1
    assert localisations[0]["nomLocalisation"] == "ipsum"


@pytest.mark.django_db(serialized_rollback=True)
def test_delete_correct_lieu(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test si j'affiche la modal de confirmation de la suppression d'une localisation,
    que je quitte la modal sans supprimer la localisation et que je supprime une autre localisation
    → vérifier que c’est la bonne localisation qui est supprimée"""
    # ajout du premier lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("lorem")
    lieu_form_elements.save_btn.click()

    # ajout du deuxième lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("ipsum")
    lieu_form_elements.save_btn.click()

    page.get_by_role("button", name="Supprimer la localisation").first.click()
    page.get_by_role("dialog", name="Supprimer").get_by_role("button", name="Fermer").click()

    page.get_by_role("button", name="Supprimer la localisation").nth(1).click()
    page.get_by_role("dialog", name="Supprimer").get_by_role("button", name="Supprimer").click()

    expect(page.locator("#localisations")).not_to_contain_text("ipsum")
    expect(page.locator("#localisations")).to_contain_text("lorem")
    elements = page.query_selector_all(".localisation-initiale")
    assert len(elements) == 1

    localisations_json = page.get_by_test_id("localisations").input_value()
    localisations = json.loads(localisations_json)
    assert len(localisations) == 1
    assert localisations[0]["nomLocalisation"] == "lorem"
