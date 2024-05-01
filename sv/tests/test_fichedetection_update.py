import pytest
from model_bakery import baker
from playwright.sync_api import Page, expect
from django.urls import reverse
from ..models import (
    FicheDetection,
)
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements


@pytest.fixture
def fiche_detection():
    return baker.make(FicheDetection, _fill_optional=True)


@pytest.fixture(autouse=True)
def test_goto_fiche_detection_update_form_url(live_server, page: Page, fiche_detection: FicheDetection):
    """Ouvre la page de modification de la fiche de détection."""
    fiche_detection_update_form_url = reverse("fiche-detection-modification", kwargs={"pk": fiche_detection.id})
    return page.goto(f"{live_server.url}{fiche_detection_update_form_url}")


def test_page_title(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, fiche_detection: FicheDetection
):
    """Test que le titre de la page est bien "Modification de la fiche détection n°2024.1"""
    expect(form_elements.title).to_contain_text(f"Modification de la fiche détection n°{fiche_detection.numero}")


def test_fiche_detection_update_page_content(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, fiche_detection: FicheDetection
):
    """Test que toutes les données de la fiche de détection sont affichées sur la page de modification de la fiche de détection."""

    # Createur
    expect(form_elements.createur_input).to_contain_text(fiche_detection.createur.nom)
    expect(form_elements.createur_input).to_have_value(str(fiche_detection.createur.id))

    # Statut évènement
    expect(form_elements.statut_evenement_input).to_contain_text(fiche_detection.statut_evenement.libelle)
    expect(form_elements.statut_evenement_input).to_have_value(str(fiche_detection.statut_evenement.id))

    # Organisme nuisible
    expect(form_elements.organisme_nuisible_input).to_contain_text(fiche_detection.organisme_nuisible.libelle_court)
    expect(form_elements.organisme_nuisible_input).to_have_value(str(fiche_detection.organisme_nuisible.id))

    # Statut règlementaire
    expect(form_elements.statut_reglementaire_input).to_contain_text(fiche_detection.statut_reglementaire.libelle)
    expect(form_elements.statut_reglementaire_input).to_have_value(str(fiche_detection.statut_reglementaire.id))

    # Contexte
    expect(form_elements.contexte_input).to_contain_text(fiche_detection.contexte.nom)
    expect(form_elements.contexte_input).to_have_value(str(fiche_detection.contexte.id))

    # Date 1er signalement
    expect(form_elements.date_1er_signalement_input).to_have_value(str(fiche_detection.date_premier_signalement))

    # Commentaire
    expect(form_elements.commentaire_input).to_have_value(fiche_detection.commentaire)

    # Mesures conservatoires immédiates
    expect(form_elements.mesures_conservatoires_immediates_input).to_have_value(
        fiche_detection.mesures_conservatoires_immediates
    )

    # Mesures de consignation
    expect(form_elements.mesures_consignation_input).to_have_value(fiche_detection.mesures_consignation)

    # Mesures phytosanitaires
    expect(form_elements.mesures_phytosanitaires_input).to_have_value(fiche_detection.mesures_phytosanitaires)

    # Mesures de surveillance spécifique
    expect(form_elements.mesures_surveillance_specifique_input).to_have_value(
        fiche_detection.mesures_surveillance_specifique
    )

    # TODO: ajouter les tests pour les lieux et les prélèvements


def test_fiche_detection_update_with_createur_only(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements
):
    """Test que la page de modification de la fiche de détection affiche uniquement le créateur pour une fiche détection contenant uniquement le créateur."""

    fiche_detection_with_createur_only = baker.make(FicheDetection)
    goto_url = reverse("fiche-detection-modification", kwargs={"pk": fiche_detection_with_createur_only.id})

    page.goto(f"{live_server.url}{goto_url}")

    expect(form_elements.createur_input).to_contain_text(fiche_detection_with_createur_only.createur.nom)
    expect(form_elements.createur_input).to_have_value(str(fiche_detection_with_createur_only.createur.id))
    expect(form_elements.statut_evenement_input).to_contain_text("----")
    expect(form_elements.statut_evenement_input).to_have_value("")
    expect(form_elements.organisme_nuisible_input).to_contain_text("----")
    expect(form_elements.organisme_nuisible_input).to_have_value("")
    expect(form_elements.statut_reglementaire_input).to_contain_text("----")
    expect(form_elements.statut_reglementaire_input).to_have_value("")
    expect(form_elements.contexte_input).to_contain_text("----")
    expect(form_elements.contexte_input).to_have_value("")
    expect(form_elements.date_1er_signalement_input).to_have_value("")
    expect(form_elements.commentaire_input).to_have_value("")
    expect(form_elements.mesures_conservatoires_immediates_input).to_have_value("")
    expect(form_elements.mesures_consignation_input).to_have_value("")
    expect(form_elements.mesures_phytosanitaires_input).to_have_value("")
    expect(form_elements.mesures_surveillance_specifique_input).to_have_value("")


def test_fiche_detection_update_without_lieux_and_prelevement(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, fiche_detection: FicheDetection
):
    """Test que les modifications des informations, objet de l'évènement et mesures de gestion sont bien enregistrées apès modification."""
    new_fiche_detection = baker.make(FicheDetection, _fill_optional=True)
    page.reload()
    form_elements.createur_input.select_option(str(new_fiche_detection.createur.id))
    form_elements.statut_evenement_input.select_option(str(new_fiche_detection.statut_evenement.id))
    # TODO
    # page.locator("#organisme-nuisible-input").select_option(str(new_organisme_nuisible.id))
    # page.locator("#organisme-nuisible").get_by_text("----").nth(1).click()
    # page.get_by_role("option", name=str(new_organisme_nuisible)).click()
    form_elements.statut_reglementaire_input.select_option(str(new_fiche_detection.statut_reglementaire.id))
    form_elements.contexte_input.select_option(str(new_fiche_detection.contexte.id))
    form_elements.date_1er_signalement_input.fill(new_fiche_detection.date_premier_signalement.strftime("%Y-%m-%d"))
    form_elements.commentaire_input.fill(new_fiche_detection.commentaire)
    form_elements.mesures_conservatoires_immediates_input.fill(new_fiche_detection.mesures_conservatoires_immediates)
    form_elements.mesures_consignation_input.fill(new_fiche_detection.mesures_consignation)
    form_elements.mesures_phytosanitaires_input.fill(new_fiche_detection.mesures_phytosanitaires)
    form_elements.mesures_surveillance_specifique_input.fill(new_fiche_detection.mesures_surveillance_specifique)
    form_elements.save_btn.click()
    page.wait_for_timeout(200)

    fiche_detection_updated = FicheDetection.objects.get(id=fiche_detection.id)
    assert fiche_detection_updated.createur == new_fiche_detection.createur
    assert fiche_detection_updated.statut_evenement == new_fiche_detection.statut_evenement
    # TODO
    # assert fiche_detection_updated.organisme_nuisible == new_organisme_nuisible
    assert fiche_detection_updated.statut_reglementaire == new_fiche_detection.statut_reglementaire
    assert fiche_detection_updated.contexte == new_fiche_detection.contexte
    assert fiche_detection_updated.commentaire == new_fiche_detection.commentaire
    assert (
        fiche_detection_updated.mesures_conservatoires_immediates
        == new_fiche_detection.mesures_conservatoires_immediates
    )
    assert fiche_detection_updated.mesures_consignation == new_fiche_detection.mesures_consignation
    assert fiche_detection_updated.mesures_phytosanitaires == new_fiche_detection.mesures_phytosanitaires
    assert (
        fiche_detection_updated.mesures_surveillance_specifique == new_fiche_detection.mesures_surveillance_specifique
    )


def test_add_new_lieu(
    live_server,
    page: Page,
    fiche_detection: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que l'ajout d'un nouveau lieu est bien enregistré."""

    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.fill("test")
    lieu_form_elements.save_btn.click()
    form_elements.save_btn.click()
    page.wait_for_timeout(200)

    fd = FicheDetection.objects.get(id=fiche_detection.id)
    assert fd.lieux.count() == 1
    assert fd.lieux.first().nom == "test"
