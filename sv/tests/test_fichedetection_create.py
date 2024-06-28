import pytest
from datetime import datetime
from playwright.sync_api import Page, expect
from django.urls import reverse
from .conftest import check_select_options
from .test_utils import FicheDetectionFormDomElements
from ..models import (
    FicheDetection,
    Unite,
    StatutEvenement,
    StatutReglementaire,
    Contexte,
)


def test_page_title(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que le titre de la page est bien "Modification de la fiche détection n°2024.1"""
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    expect(form_elements.title).to_contain_text("Création d'une fiche détection")


def test_new_fiche_detection_form_content(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que la page de création de fiche de détection contient bien les labels et les champs attendus."""
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    expect(form_elements.informations_title).to_be_visible()
    expect(form_elements.objet_evenement_title).to_be_visible()
    expect(form_elements.lieux_title).to_be_visible()
    expect(form_elements.prelevements_title).to_be_visible()
    expect(form_elements.mesures_gestion_title).to_be_visible()
    expect(form_elements.save_btn).to_be_visible()
    expect(form_elements.add_lieu_btn).to_be_visible()
    expect(form_elements.add_prelevement_btn).to_be_hidden()

    expect(form_elements.date_creation_label).to_be_visible()
    expect(form_elements.date_creation_input).to_be_disabled()

    expect(form_elements.createur_label).to_be_visible()
    expect(form_elements.createur_input).to_be_visible()
    expect(form_elements.createur_input).to_contain_text("----")
    expect(form_elements.createur_input).to_have_value("")
    unites = list(Unite.objects.values_list("nom", flat=True))
    check_select_options(page, "Créateur", unites)

    expect(form_elements.statut_evenement_label).to_be_visible()
    expect(form_elements.statut_evenement_input).to_be_visible()
    expect(form_elements.statut_evenement_input).to_contain_text("----")
    expect(form_elements.statut_evenement_input).to_have_value("")
    statuts_evenement = list(StatutEvenement.objects.values_list("libelle", flat=True))
    check_select_options(page, "Statut évènement", statuts_evenement)

    expect(form_elements.organisme_nuisible_label).to_be_visible()
    expect(form_elements.organisme_nuisible_input).to_contain_text("----")

    expect(form_elements.statut_reglementaire_label).to_be_visible()
    expect(form_elements.statut_reglementaire_input).to_be_visible()
    expect(form_elements.statut_reglementaire_input).to_contain_text("----")
    expect(form_elements.statut_reglementaire_input).to_have_value("")
    statuts_reglementaire = list(StatutReglementaire.objects.values_list("libelle", flat=True))
    check_select_options(page, "Statut règlementaire", statuts_reglementaire)

    expect(form_elements.contexte_label).to_be_visible()
    expect(form_elements.contexte_input).to_be_visible()
    expect(form_elements.contexte_input).to_contain_text("----")
    expect(form_elements.contexte_input).to_have_value("")
    contextes = list(Contexte.objects.values_list("nom", flat=True))
    check_select_options(page, "Contexte", contextes)

    expect(form_elements.date_1er_signalement_label).to_be_visible()
    expect(form_elements.date_1er_signalement_input).to_be_visible()
    expect(form_elements.date_1er_signalement_input).to_be_empty()

    expect(form_elements.commentaire_label).to_be_visible()
    expect(form_elements.commentaire_input).to_be_visible()
    expect(form_elements.commentaire_input).to_be_empty()

    expect(form_elements.mesures_conservatoires_immediates_label).to_be_visible()
    expect(form_elements.mesures_conservatoires_immediates_input).to_be_visible()
    expect(form_elements.mesures_conservatoires_immediates_input).to_be_empty()

    expect(form_elements.mesures_conservatoires_immediates_label).to_be_visible()
    expect(form_elements.mesures_conservatoires_immediates_input).to_be_visible()
    expect(form_elements.mesures_conservatoires_immediates_input).to_be_empty()

    expect(form_elements.mesures_phytosanitaires_label).to_be_visible()
    expect(form_elements.mesures_phytosanitaires_input).to_be_visible()
    expect(form_elements.mesures_phytosanitaires_input).to_be_empty()

    expect(form_elements.mesures_surveillance_specifique_label).to_be_visible()
    expect(form_elements.mesures_surveillance_specifique_input).to_be_visible()
    expect(form_elements.mesures_surveillance_specifique_input).to_be_empty()


def test_date_creation_field_is_current_day(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que la date de création soit egale à la date du jour"""
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    expect(form_elements.date_creation_input).to_have_value(datetime.now().strftime("%d/%m/%Y"))


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_fiche_detection_create_without_lieux_and_prelevement(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements
):
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    """Test que les informations de la fiche de détection sont bien enregistrées après création."""
    page.get_by_label("Créateur").select_option(label="Mission des urgences sanitaires")
    page.get_by_label("Statut évènement").select_option(label="Foyer")
    page.get_by_text("--------").click()
    page.get_by_label("----").fill("xylela")
    page.get_by_role("option", name="Xylella fastidiosa (maladie de Pierce)").click()
    page.get_by_label("Statut règlementaire").select_option("2")
    page.get_by_label("Contexte").select_option("2")
    page.get_by_label("Date 1er signalement").fill("2024-04-21")
    page.get_by_label("Commentaire").click()
    page.get_by_label("Commentaire").fill("test commentaire")
    page.get_by_label("Mesures conservatoires immé").click()
    page.get_by_label("Mesures conservatoires immé").fill("test mesures conservatoires")
    page.get_by_label("Mesures de consignation").click()
    page.get_by_label("Mesures de consignation").fill("test mesures consignation")
    page.get_by_label("Mesures phytosanitaires").click()
    page.get_by_label("Mesures phytosanitaires").fill("test mesures phyto")
    page.get_by_label("Mesures de surveillance spé").click()
    page.get_by_label("Mesures de surveillance spé").fill("test mesures surveillance")
    page.get_by_role("button", name="Enregistrer").click()

    page.wait_for_timeout(500)

    fiche_detection = FicheDetection.objects.get()
    assert fiche_detection.createur.nom == "Mission des urgences sanitaires"
    assert fiche_detection.statut_evenement.libelle == "Foyer"
    assert fiche_detection.organisme_nuisible.libelle_court == "Xylella fastidiosa (maladie de Pierce)"
    assert fiche_detection.statut_reglementaire.id == 2
    assert fiche_detection.contexte.id == 2
    assert fiche_detection.date_premier_signalement.strftime("%Y-%m-%d") == "2024-04-21"
    assert fiche_detection.commentaire == "test commentaire"
    assert fiche_detection.mesures_conservatoires_immediates == "test mesures conservatoires"
    assert fiche_detection.mesures_consignation == "test mesures consignation"
    assert fiche_detection.mesures_phytosanitaires == "test mesures phyto"
    assert fiche_detection.mesures_surveillance_specifique == "test mesures surveillance"
