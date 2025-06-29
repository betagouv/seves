import re

import pytest
from playwright.sync_api import Page, expect
from django.urls import reverse

from core.models import Region, Departement
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements, PrelevementFormDomElements
from ..factories import EvenementFactory, FicheDetectionFactory
from ..models import StructurePreleveuse, Prelevement

from sv.constants import STRUCTURES_PRELEVEUSES


@pytest.fixture(autouse=True)
def create_fixtures_if_needed(db):
    for nom in STRUCTURES_PRELEVEUSES:
        StructurePreleveuse.objects.get_or_create(nom=nom)


@pytest.fixture(autouse=True)
def test_goto_fiche_detection_creation_url(live_server, page: Page):
    """Ouvre la page de création d'une fiche de détection"""
    region, _ = Region.objects.get_or_create(nom="Hauts-de-France")
    Departement.objects.get_or_create(numero=59, nom="Nord", region=region)
    add_fiche_detection_form_url = reverse("sv:fiche-detection-creation")
    return page.goto(f"{live_server.url}{add_fiche_detection_form_url}")


def _add_new_lieu(
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
    extra_str="",
    extra_int=0,
):
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill(f"nom lieu{extra_str}")
    lieu_form_elements.force_adresse(lieu_form_elements.adresse_choicesjs, f"une adresse{extra_str}")

    page.wait_for_timeout(100)

    lieu_form_elements.force_commune()
    lieu_form_elements.coord_gps_wgs84_latitude_input.click()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(1 + extra_int))
    lieu_form_elements.coord_gps_wgs84_longitude_input.click()
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(2 + extra_int))
    lieu_form_elements.save_btn.click()


def _check_add_lieu_form_fields_are_empty(page: Page, lieu_form_elements: LieuFormDomElements):
    """Vérifie que le formulaire d'ajout d'un lieu est vide"""
    expect(lieu_form_elements.nom_input).to_be_empty()
    expect(lieu_form_elements.adresse_input).to_be_empty()
    expect(lieu_form_elements.commune_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_be_empty()


# =============
# Partie Informations, Objet de l'évènement, Mesures de gestion
# =============


def test_date_creation_field_is_disabled(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que le champ Date de création est désactivé"""
    expect(form_elements.date_creation_input).to_be_disabled()


# =============
# Partie Lieux
# =============

# Ajouter un lieu


def test_add_lieu_button(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que le bouton Ajouter un lieu affiche le formulaire d’ajout d’une nouveau lieu dans la modal"""
    form_elements.add_lieu_btn.click()
    expect(page.get_by_role("dialog")).to_be_visible()


def test_close_button_of_add_lieu_form_modal(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que le bouton Fermer ferme la modal d'ajout d'un lieu"""
    form_elements.add_lieu_btn.click()
    page.get_by_role("button", name="Fermer").click()
    expect(page.get_by_role("dialog")).to_be_hidden()


def test_cancel_button_of_add_lieu_form_modal(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le bouton Annuler ferme la modal d'ajout d'un lieu"""
    form_elements.add_lieu_btn.click()
    lieu_form_elements.cancel_btn.click()
    expect(page.get_by_role("dialog")).to_be_hidden()


def test_add_lieu_form_have_all_fields(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le formulaire d'ajout d'un lieu contient bien les champs attendus."""
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.close_btn).to_be_visible()
    expect(lieu_form_elements.close_btn).to_have_text("Fermer")

    expect(lieu_form_elements.title).to_be_visible()
    expect(lieu_form_elements.title).to_have_text("Ajouter un lieu")

    expect(lieu_form_elements.nom_label).to_be_visible()
    expect(lieu_form_elements.nom_label).to_have_text("Nom du lieu")
    expect(lieu_form_elements.nom_input).to_be_visible()
    expect(lieu_form_elements.nom_input).to_be_empty()

    expect(lieu_form_elements.adresse_label).to_be_visible()
    expect(lieu_form_elements.adresse_label).to_have_text("Adresse ou lieu-dit")
    expect(lieu_form_elements.adresse_input).to_be_empty()

    expect(lieu_form_elements.commune_label).to_be_visible()
    expect(lieu_form_elements.commune_label).to_have_text("Commune")
    expect(lieu_form_elements.commune_input).to_be_empty()

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


def test_nom_lieu_is_required_in_add_lieu_form(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le champ Nom du lieu est requis pour l'ajout d'un lieu"""
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.nom_input).to_have_attribute("required", "")


def test_coordonnees_gps_are_numeric_in_add_lieu_form(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que les champs de coordonnées GPS (WGS84) sont des champs numériques"""
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_have_attribute("type", "number")
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_have_attribute("type", "number")


def test_description_activite_have_max_length(
    page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    form_elements.add_lieu_btn.click()
    lieu_form_elements.is_etablissement_checkbox.click(force=True)
    expect(lieu_form_elements.activite_etablissement_input).to_have_attribute("maxlength", "100")
    lieu_form_elements.activite_etablissement_input.fill("a" * 101)
    expect(lieu_form_elements.activite_etablissement_input).to_have_value("a" * 100)


def test_description_activite_counter_behavior(
    page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    form_elements.add_lieu_btn.click()
    lieu_form_elements.is_etablissement_checkbox.click(force=True)
    counter = page.locator(".character-counter").first

    expect(counter).to_be_visible()
    expect(counter).to_have_text("100 caractères restants")

    lieu_form_elements.activite_etablissement_input.fill("a" * 50)
    expect(counter).to_have_text("50 caractères restants")

    lieu_form_elements.activite_etablissement_input.fill("a" * 101)
    expect(counter).to_have_text("0 caractères restants")


def test_add_lieu_to_list(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le lieu ajouté est bien visible dans la liste des lieux"""
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test lieu")
    lieu_form_elements.save_btn.click()
    expect(page.locator("#lieux").get_by_text("test lieu")).to_be_visible()
    assert len(page.locator("#lieux-list").locator(".lieu-initial").all()) == 1


def test_added_lieu_content_in_list(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que le contenu du lieu ajouté contient le nom du lieu, la commune et les boutons de suppression et de modification"""
    _add_new_lieu(page, form_elements, lieu_form_elements)
    expect(page.locator("#lieux").get_by_text("nom lieu")).to_be_visible()
    expect(page.locator("#lieux")).to_contain_text("nom lieu")
    expect(page.get_by_text("Lille", exact=True)).to_be_visible()
    expect(page.locator("#lieux")).to_contain_text("Lille")
    expect(page.get_by_role("button", name="Modifier le lieu")).to_be_visible()
    expect(page.get_by_role("button", name="Supprimer le lieu")).to_be_visible()


def test_add_two_lieux_to_list(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que les lieux ajoutés sont bien visibles dans la liste des lieux"""
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test lieu")
    lieu_form_elements.save_btn.click()

    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test lieu 2")
    lieu_form_elements.save_btn.click()

    expect(page.locator("#lieux").get_by_text("test lieu", exact=True)).to_be_visible()
    expect(page.locator("#lieux").get_by_text("test lieu 2", exact=True)).to_be_visible()
    expect(page.locator("#lieux")).to_contain_text("a")
    expect(page.locator("#lieux")).to_contain_text("b")
    assert len(page.locator("#lieux-list").locator(".lieu-initial").all()) == 2


# Modifier un lieu


def test_edit_lieu_button_show_form_in_modal(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que le bouton Modifier le lieu affiche le formulaire de modification dans une modal"""
    _add_new_lieu(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Modifier le lieu").click()

    expect(page.get_by_role("dialog")).to_be_visible()


def test_edit_lieu_modal_title_and_actions_btn(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que le titre de la modal de modification d'un lieu est bien 'Modifier le lieu'"""
    _add_new_lieu(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Modifier le lieu").click()

    expect(page.get_by_role("heading", name="Modifier le lieu")).to_be_visible()
    expect(lieu_form_elements.title).to_have_text("Modifier le lieu")
    expect(lieu_form_elements.save_btn).to_have_text("Enregistrer")


def test_edit_lieu_form_with_only_nom_lieu(
    live_server, page: Page, lieu_form_elements: LieuFormDomElements, form_elements: FicheDetectionFormDomElements
):
    """Lors de la modification d'un lieu contenant seulement le nom, seulement le champ nom du lieu est pré-rempli, les autres champs sont vides."""
    # ajout d'un lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("test lieu")
    lieu_form_elements.save_btn.click()

    page.get_by_role("button", name="Modifier le lieu").click()

    expect(lieu_form_elements.nom_input).to_have_value("test lieu")
    expect(lieu_form_elements.adresse_input).to_be_empty()
    expect(lieu_form_elements.commune_input).to_be_empty()
    expect(lieu_form_elements.code_insee_hidden_input).to_be_empty()
    expect(lieu_form_elements.departement_hidden_input).to_have_value("")
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_be_empty()


def test_edit_lieu_form_have_all_fields(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que le formulaire de modification d'un lieu contient bien les champs attendus et que ceux-ci sont pré-remplis avec les valeurs du lieu à modifier."""
    _add_new_lieu(page, form_elements, lieu_form_elements)
    # modification du lieu
    page.get_by_role("button", name="Modifier le lieu").click()

    expect(lieu_form_elements.close_btn).to_be_visible()
    expect(lieu_form_elements.close_btn).to_have_text("Fermer")

    expect(page.get_by_role("heading", name="Modifier le lieu")).to_be_visible()
    expect(lieu_form_elements.title).to_have_text("Modifier le lieu")

    expect(lieu_form_elements.nom_label).to_be_visible()
    expect(lieu_form_elements.nom_label).to_have_text("Nom du lieu")
    expect(lieu_form_elements.nom_input).to_be_visible()
    expect(lieu_form_elements.nom_input).to_have_value("nom lieu")

    expect(lieu_form_elements.adresse_label).to_be_visible()
    expect(lieu_form_elements.adresse_label).to_have_text("Adresse ou lieu-dit")
    expect(lieu_form_elements.adresse_input).to_have_value("une adresse")

    expect(lieu_form_elements.commune_hidden_input).to_have_value("Lille")
    expect(lieu_form_elements.code_insee_hidden_input).to_have_value("59350")
    expect(page.get_by_text("Lille (59)Remove item")).to_be_visible()
    expect(lieu_form_elements.departement_hidden_input).to_have_value("59")

    expect(lieu_form_elements.coord_gps_wgs84_latitude_label).to_be_visible()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_label).to_have_text("Coordonnées GPS (WGS84)")
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_be_visible()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_have_value("1")
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_be_visible()
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_have_value("2")


@pytest.mark.django_db
def test_edit_lieu_form_have_all_fields_with_multiple_lieux(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que le formulaire de modification d'un lieu contient bien les champs attendus
    et que ceux-ci sont pré-remplis avec les valeurs du lieu à modifier si plusieurs lieux sont présentent dans la liste"""
    _add_new_lieu(page, form_elements, lieu_form_elements)
    _add_new_lieu(page, form_elements, lieu_form_elements, extra_str=" 2", extra_int=2)

    # vérification des valeurs du premier lieu
    page.get_by_role("button", name="Modifier le lieu").first.click()
    expect(lieu_form_elements.nom_input).to_have_value("nom lieu")
    expect(lieu_form_elements.adresse_input).to_have_value("une adresse")
    expect(lieu_form_elements.commune_hidden_input).to_have_value("Lille")
    expect(lieu_form_elements.code_insee_hidden_input).to_have_value("59350")
    expect(lieu_form_elements.departement_hidden_input).to_have_value("59")
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_have_value("1")
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_have_value("2")
    page.get_by_role("button", name="Fermer").click()

    # vérification des valeurs du deuxième lieu
    page.get_by_role("button", name="Modifier le lieu").nth(1).click()
    expect(lieu_form_elements.nom_input).to_have_value("nom lieu 2")
    expect(lieu_form_elements.adresse_input).to_have_value("une adresse 2")
    expect(lieu_form_elements.commune_hidden_input).to_have_value("Lille")
    expect(lieu_form_elements.code_insee_hidden_input).to_have_value("59350")
    expect(lieu_form_elements.departement_hidden_input).to_have_value("59")
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_have_value("3")
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_have_value("4")
    page.get_by_role("button", name="Fermer").click()


def test_add_lieu_form_is_empty_after_edit(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que le formulaire d'ajout d'un lieu est vide après la modification d'un lieu"""
    # ajout d'un lieu
    _add_new_lieu(page, form_elements, lieu_form_elements)

    # modification du lieu
    page.get_by_role("button", name="Modifier le lieu").click()
    lieu_form_elements.nom_input.fill("nom lieu modifié")
    lieu_form_elements.force_adresse(lieu_form_elements.adresse_choicesjs, "une adresse modifiée")
    lieu_form_elements.force_commune()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill("11")
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill("21")
    lieu_form_elements.save_btn.click()

    # vérification que le formulaire d'ajout d'un lieu est vide
    form_elements.add_lieu_btn.click()
    expect(lieu_form_elements.nom_input).to_be_empty()
    expect(lieu_form_elements.adresse_input).to_be_empty()
    expect(lieu_form_elements.commune_input).to_be_empty()
    expect(lieu_form_elements.code_insee_hidden_input).to_be_empty()
    expect(lieu_form_elements.departement_hidden_input).to_have_value("")
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_be_empty()
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_be_empty()


def test_add_lieu_form_is_empty_after_close_edit_form_with_close_btn_without_save(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que si je quitte la modification d’un lieu sans enregistrer via le  bouton fermer,
    je dois trouver le formulaire d’ajout d’un lieu vide"""
    _add_new_lieu(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Modifier le lieu").click()
    page.get_by_role("button", name="Fermer").click()
    form_elements.add_lieu_btn.click()

    _check_add_lieu_form_fields_are_empty(page, lieu_form_elements)


def test_add_lieu_form_is_empty_after_close_edit_form_with_cancel_btn_without_save(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que si je quitte la modification d’un lieu sans enregistrer via le bouton annuler,
    je dois trouver le formulaire d’ajout d’un lieu vide"""
    _add_new_lieu(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Modifier le lieu").click()
    page.get_by_label("Modifier le lieu").get_by_role("link", name="Annuler").click()
    form_elements.add_lieu_btn.click()

    _check_add_lieu_form_fields_are_empty(page, lieu_form_elements)


def test_add_lieu_form_is_empty_after_close_edit_form_with_esc_key_without_save(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que si je quitte la modification d’un lieu sans enregistrer via la touche echap du clavier,
    je dois trouver le formulaire d’ajout d’un lieu vide"""
    _add_new_lieu(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Modifier le lieu").click()
    page.keyboard.press("Escape")
    form_elements.add_lieu_btn.click()

    _check_add_lieu_form_fields_are_empty(page, lieu_form_elements)


# Supprimer un lieu


def test_delete_lieu_button_show_confirmation_modal(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test qu'une modal de confirmation est affichée lors de la suppression d'un lieu liée à aucun prélèvement"""
    _add_new_lieu(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Supprimer le lieu").click()

    expect(page.get_by_role("dialog")).to_be_visible()


def test_delete_lieu_from_list(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que le lieu est bien supprimée de la liste des lieux après confirmation"""
    _add_new_lieu(page, form_elements, lieu_form_elements)

    page.get_by_role("button", name="Supprimer le lieu").click()
    page.get_by_role("dialog", name="Supprimer").get_by_role("button", name="Supprimer").click()

    expect(page.locator("#lieux")).not_to_contain_text("nom lieu")
    assert len(page.locator("#lieux-list").locator(".lieu-initial").all()) == 0


def test_delete_lieu_from_list_with_multiple_lieux(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test que le lieu est bien supprimé de la liste des lieux après confirmation
    et que c'est le bon lieu qui est supprimé"""
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
    page.get_by_role("button", name="Supprimer le lieu").first.click()
    page.get_by_role("dialog", name="Supprimer").get_by_role("button", name="Supprimer").click()

    expect(page.locator("#lieux")).not_to_contain_text("lorem")
    expect(page.locator("#lieux")).to_contain_text("ipsum")
    assert len(page.locator("#lieux-list").locator(".lieu-initial").all()) == 1
    assert page.evaluate("document.lieuxCards") == [{"commune": "", "id": "1", "nom": "ipsum"}]


def test_delete_correct_lieu(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    """Test si j'affiche la modale de confirmation de la suppression d'un lieu,
    que je quitte la modale sans supprimer le lieu et que je supprime un autre lieu
    → vérifier que c’est le bon lieu qui est supprimé"""
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

    page.get_by_role("button", name="Supprimer le lieu").first.click()
    page.locator(".fr-btn--close").locator("visible=true").click()
    page.get_by_role("button", name="Supprimer le lieu").nth(1).click()
    page.get_by_role("dialog", name="Supprimer").get_by_role("button", name="Supprimer").click()

    expect(page.locator("#lieux")).not_to_contain_text("ipsum")
    expect(page.locator("#lieux")).to_contain_text("lorem")
    assert len(page.locator("#lieux-list").locator(".lieu-initial").all()) == 1

    cards = page.evaluate("document.lieuxCards")
    assert len(cards) == 1
    assert cards[0]["commune"] == ""
    assert cards[0]["nom"] == "lorem"


@pytest.mark.django_db
def test_delete_lieu_is_not_possible_if_linked_to_prelevement(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    page.wait_for_timeout(600)

    """Test que la suppression d'un lieu est impossible si il est lié à un prélèvement"""
    # ajout d'un lieu
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("lorem")
    lieu_form_elements.save_btn.click()

    # ajout d'un prélèvement
    form_elements.add_prelevement_btn.click()
    prelevement_form_elements = PrelevementFormDomElements(page)
    prelevement_form_elements.date_prelevement_input.click()
    assert StructurePreleveuse.objects.count() > 0
    prelevement_form_elements.structure_input.select_option(value=str(StructurePreleveuse.objects.first().id))
    prelevement_form_elements.date_prelevement_input.fill("2021-01-01")
    prelevement_form_elements.resultat_input(Prelevement.Resultat.DETECTE).click()
    prelevement_form_elements.type_analyse_input("première intention").click()
    prelevement_form_elements.save_btn.click()

    # suppression du lieu
    page.get_by_role("button", name="Supprimer le lieu").click()

    expect(page.get_by_role("dialog")).to_be_visible()
    page.get_by_role("button", name="Fermer").click()
    expect(page.locator("#lieux")).to_contain_text("lorem")
    assert len(page.locator("#lieux-list").locator(".lieu-initial").all()) == 1
    assert page.evaluate("document.lieuxCards") == [{"commune": "", "id": "0", "nom": "lorem"}]


# =============
# Partie Prélèvements
# =============

# Ajouter un prélèvement


def test_add_prelevement_btn_disabled_if_no_lieu(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    expect(form_elements.add_prelevement_btn).to_be_disabled()


def test_add_prelevement_btn_is_visible_if_lieu_exists(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que le bouton d'ajout d'un prélèvement est visible si au moins un lieu existe dans la liste"""
    _add_new_lieu(page, form_elements, lieu_form_elements)
    expect(form_elements.add_prelevement_btn).to_be_visible()
    expect(form_elements.add_prelevement_btn).to_be_enabled()


def test_numero_rapport_inspection_format(page):
    inputs_rapport_inspection = page.locator("input[name^='prelevements-'][name$='-numero_rapport_inspection']").all()
    assert all(input.get_attribute("pattern") == "^\\d{2}-\\d{6}$" for input in inputs_rapport_inspection)


def test_info_message_in_prelevement_bloc_should_be_visible_without_locations(
    page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements
):
    expect(page.locator("#no-lieux-text")).to_be_visible()

    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.fill("un lieu")
    lieu_form_elements.save_btn.click()
    page.get_by_role("button", name="Supprimer le lieu").click()
    page.get_by_role("dialog", name="Supprimer").get_by_role("button", name="Supprimer").click()

    expect(page.locator("#no-lieux-text")).to_be_visible()


@pytest.mark.django_db
def test_prelevement_resultat_card(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test le bon affichage du résultat dans la liste des prélèvements"""
    # Ajout d'un lieu nécessaire pour pouvoir ajouter un prélèvement
    _add_new_lieu(page, form_elements, lieu_form_elements)

    # Ajout du prélèvement initial (Détecté)
    form_elements.add_prelevement_btn.click()
    prelevement_form_elements = PrelevementFormDomElements(page)
    prelevement_form_elements.structure_input.select_option(value=str(StructurePreleveuse.objects.first().id))
    prelevement_form_elements.resultat_input(Prelevement.Resultat.DETECTE).click()
    prelevement_form_elements.type_analyse_input("première intention").click()
    prelevement_form_elements.save_btn.click()
    expect(page.locator("#prelevements-list")).to_contain_text("DÉTECTÉ")

    # Modification du statut à "Non détecté"
    page.locator("#prelevements-list").get_by_role("button").first.click()
    prelevement_form_elements.resultat_input(Prelevement.Resultat.NON_DETECTE).click()
    prelevement_form_elements.save_btn.click()
    expect(page.locator("#prelevements-list")).to_contain_text("NON DÉTECTÉ")

    # Modification du statut à "Non conclusif"
    page.locator("#prelevements-list").get_by_role("button").first.click()
    prelevement_form_elements.resultat_input(Prelevement.Resultat.NON_CONCLUSIF).click()
    prelevement_form_elements.save_btn.click()
    expect(page.locator("#prelevements-list")).to_contain_text("NON CONCLUSIF")


@pytest.mark.parametrize("action_name", ["Ajouter une détection", "Modifier"])
def test_return_to_correct_detection_after_creation_or_update(live_server, page: Page, action_name):
    evenement = EvenementFactory()
    _, detection_2, _ = FicheDetectionFactory.create_batch(3, evenement=evenement)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}?detection={detection_2.pk}")

    page.get_by_role("link", name=action_name).click()
    page.get_by_role("link", name="Annuler").click()

    expect(page.get_by_role("tab", name=f"{detection_2.numero}")).to_be_visible()
    expect(page.get_by_role("tab", name=f"{detection_2.numero}")).to_have_class(re.compile(r"(^|\s)selected($|\s)"))


def test_add_prelevement_en_attente_show_modal(
    page: Page, form_elements: FicheDetectionFormDomElements, lieu_form_elements: LieuFormDomElements, choice_js_fill
):
    _add_new_lieu(page, form_elements, lieu_form_elements)
    form_elements.add_prelevement_btn.click()
    prelevement_form_elements = PrelevementFormDomElements(page)
    prelevement_form_elements.type_analyse_input("première intention").click()
    prelevement_form_elements.structure_input.select_option(value=str(StructurePreleveuse.objects.first().id))
    prelevement_form_elements.resultat_input(Prelevement.Resultat.EN_ATTENTE).click()
    prelevement_form_elements.save_btn.click()

    expect(page.locator("#modal-add-edit-prelevement-0")).to_be_hidden(timeout=500)
    expect(page.locator("#fr-modal-prelevement-en-attente")).to_be_visible()
    expect(page.get_by_role("heading", name="Prélèvement en attente"))
