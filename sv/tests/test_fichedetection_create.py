import pytest
from model_bakery import baker
from datetime import datetime
from playwright.sync_api import Page, expect
from django.urls import reverse
from .conftest import check_select_options
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements
from ..models import (
    FicheDetection,
    StatutEvenement,
    StatutReglementaire,
    Contexte,
    OrganismeNuisible,
    Lieu,
    Departement,
    TypeExploitant,
    PositionChaineDistribution,
)

from sv.constants import STATUTS_EVENEMENT, STATUTS_REGLEMENTAIRES, CONTEXTES


@pytest.fixture(autouse=True)
@pytest.mark.db
def create_fixtures_if_needed():
    for statut in STATUTS_EVENEMENT:
        StatutEvenement.objects.get_or_create(libelle=statut)

    OrganismeNuisible.objects.get_or_create(libelle_court="Xylella fastidiosa (maladie de Pierce)")
    OrganismeNuisible.objects.get_or_create(libelle_court="lorem ipsum")

    for code, libelle in STATUTS_REGLEMENTAIRES.items():
        StatutReglementaire.objects.get_or_create(code=code, libelle=libelle)

    for contexte in CONTEXTES:
        Contexte.objects.get_or_create(nom=contexte)


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


@pytest.mark.django_db
def test_fiche_detection_create_without_lieux_and_prelevement(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, mocked_authentification_user
):
    statut_evenement = StatutEvenement.objects.first()
    organisme_nuisible = OrganismeNuisible.objects.get(libelle_court="Xylella fastidiosa (maladie de Pierce)")
    statut_reglementaire = StatutReglementaire.objects.first()
    contexte = Contexte.objects.first()

    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    """Test que les informations de la fiche de détection sont bien enregistrées après création."""
    page.get_by_label("Statut évènement").select_option(value=str(statut_evenement.id))
    page.get_by_text("--------").click()
    page.get_by_label("----").fill("xylela")
    page.get_by_role("option", name=organisme_nuisible.libelle_court).click()
    page.get_by_label("Statut règlementaire").select_option(value=str(statut_reglementaire.id))
    page.get_by_label("Contexte").select_option(value=str(contexte.id))
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

    page.wait_for_timeout(600)

    fiche_detection = FicheDetection.objects.get()
    assert fiche_detection.createur == mocked_authentification_user.agent.structure
    assert fiche_detection.statut_evenement.libelle == statut_evenement.libelle
    assert fiche_detection.organisme_nuisible.libelle_court == organisme_nuisible.libelle_court
    assert fiche_detection.statut_reglementaire.id == statut_reglementaire.id
    assert fiche_detection.contexte.id == contexte.id
    assert fiche_detection.date_premier_signalement.strftime("%Y-%m-%d") == "2024-04-21"
    assert fiche_detection.commentaire == "test commentaire"
    assert fiche_detection.mesures_conservatoires_immediates == "test mesures conservatoires"
    assert fiche_detection.mesures_consignation == "test mesures consignation"
    assert fiche_detection.mesures_phytosanitaires == "test mesures phyto"
    assert fiche_detection.mesures_surveillance_specifique == "test mesures surveillance"

    page.get_by_test_id("contacts").click()
    expect(page.get_by_text(str(mocked_authentification_user.agent), exact=True)).to_be_visible()


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_create_fiche_detection_with_lieu(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
    mocked_authentification_user,
):
    dept = baker.make(Departement)
    type_exploitant = baker.make(TypeExploitant)
    position = baker.make(PositionChaineDistribution)
    lieu = baker.prepare(
        Lieu,
        wgs84_latitude=48.8566,
        wgs84_longitude=2.3522,
        lambert93_latitude=6000000,
        lambert93_longitude=200000,
        code_insee="17000",
        siret_etablissement="12345678901234",
        departement=dept,
        is_etablissement=True,
        type_exploitant_etablissement=type_exploitant,
        position_chaine_distribution_etablissement=position,
        _fill_optional=True,
    )

    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    form_elements.statut_evenement_input.select_option(label="Foyer")
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.fill(lieu.nom)
    lieu_form_elements.adresse_input.fill(lieu.adresse_lieu_dit)
    lieu_form_elements.commune_input.fill(lieu.commune)
    lieu_form_elements.code_insee_input.fill(lieu.code_insee)
    lieu_form_elements.departement_input.select_option(str(lieu.departement.id))
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill(str(lieu.lambert93_latitude))
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill(str(lieu.lambert93_longitude))
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(lieu.wgs84_latitude))
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(lieu.wgs84_longitude))
    lieu_form_elements.is_etablissement_checkbox.click()
    lieu_form_elements.nom_etablissement_input.fill(lieu.nom)
    lieu_form_elements.activite_etablissement_input.fill(lieu.activite_etablissement)
    lieu_form_elements.pays_etablissement_input.fill(lieu.pays_etablissement)
    lieu_form_elements.raison_sociale_etablissement_input.fill(lieu.raison_sociale_etablissement)
    lieu_form_elements.adresse_etablissement_input.fill(lieu.adresse_etablissement)
    lieu_form_elements.siret_etablissement_input.fill(lieu.siret_etablissement)
    lieu_form_elements.type_etablissement_input.select_option(str(lieu.type_exploitant_etablissement.id))
    lieu_form_elements.position_etablissement_input.select_option(
        str(lieu.position_chaine_distribution_etablissement.id)
    )
    lieu_form_elements.save_btn.click()
    form_elements.save_btn.click()

    page.wait_for_timeout(500)

    fiche_detection = FicheDetection.objects.last()
    assert fiche_detection.lieux.count() == 1
    lieu = fiche_detection.lieux.first()
    assert lieu.nom == lieu.nom
    assert lieu.wgs84_latitude == lieu.wgs84_latitude
    assert lieu.wgs84_longitude == lieu.wgs84_longitude
    assert lieu.lambert93_latitude == lieu.lambert93_latitude
    assert lieu.lambert93_longitude == lieu.lambert93_longitude
    assert lieu.adresse_lieu_dit == lieu.adresse_lieu_dit
    assert lieu.commune == lieu.commune
    assert lieu.code_insee == str(lieu.code_insee)
    assert lieu.departement == lieu.departement
    assert lieu.is_etablissement == lieu.is_etablissement
    assert lieu.nom_etablissement == lieu.nom_etablissement
    assert lieu.activite_etablissement == lieu.activite_etablissement
    assert lieu.pays_etablissement == lieu.pays_etablissement
    assert lieu.raison_sociale_etablissement == lieu.raison_sociale_etablissement
    assert lieu.adresse_etablissement == lieu.adresse_etablissement
    assert lieu.siret_etablissement == lieu.siret_etablissement
    assert lieu.type_exploitant_etablissement == lieu.type_exploitant_etablissement
    assert lieu.position_chaine_distribution_etablissement == lieu.position_chaine_distribution_etablissement
