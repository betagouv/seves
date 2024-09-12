import pytest
from model_bakery import baker
from playwright.sync_api import Page, expect
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from ..models import (
    FicheDetection,
    Lieu,
    Prelevement,
    Departement,
    TypeExploitant,
    PositionChaineDistribution,
)
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements, PrelevementFormDomElements


def get_fiche_detection_update_form_url(fiche_detection: FicheDetection):
    return reverse("fiche-detection-modification", kwargs={"pk": fiche_detection.id})


@pytest.fixture
def fiche_detection_with_one_lieu(fiche_detection, db):
    baker.make(Lieu, fiche_detection=fiche_detection, _fill_optional=True)
    return fiche_detection


@pytest.fixture
def fiche_detection_with_two_lieux(fiche_detection, db):
    baker.make(Lieu, fiche_detection=fiche_detection, _fill_optional=True)
    baker.make(Lieu, fiche_detection=fiche_detection, _fill_optional=True)
    return fiche_detection


@pytest.fixture
def fiche_detection_with_one_lieu_and_one_prelevement(fiche_detection, db):
    lieu = baker.make(Lieu, fiche_detection=fiche_detection, _fill_optional=True)
    baker.make(Prelevement, lieu=lieu, _fill_optional=True)
    return fiche_detection


def test_page_title(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, fiche_detection: FicheDetection
):
    """Test que le titre de la page est bien "Modification de la fiche détection n°2024.1"""
    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection)}")
    expect(form_elements.title).to_contain_text(f"Modification de la fiche détection n°{fiche_detection.numero}")


def test_fiche_detection_update_page_content(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, fiche_detection: FicheDetection
):
    """Test que toutes les données de la fiche de détection sont affichées sur la page de modification de la fiche de détection."""

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection)}")

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


def test_fiche_detection_update_page_content_with_no_data(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements
):
    """Test que la page de modification de la fiche de détection affiche aucune donnée pour une fiche détection sans données"""

    fiche_detection = baker.make(FicheDetection)

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection)}")

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


@pytest.mark.django_db
def test_fiche_detection_update_without_lieux_and_prelevement(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    fiche_detection: FicheDetection,
    fiche_detection_bakery,
    mocked_authentification_user,
):
    """Test que les modifications des informations, objet de l'évènement et mesures de gestion sont bien enregistrées en base de données apès modification."""

    new_fiche_detection = fiche_detection_bakery()

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection)}")
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
    page.wait_for_timeout(600)

    fiche_detection_updated = FicheDetection.objects.get(id=fiche_detection.id)
    assert (
        fiche_detection_updated.createur == fiche_detection.createur
    )  # le createur ne doit pas changer lors d'une modification
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


@pytest.mark.django_db
def test_add_new_lieu(
    live_server,
    page: Page,
    fiche_detection: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que l'ajout d'un nouveau lieu est bien enregistré en base de données."""
    lieu = baker.prepare(
        Lieu,
        wgs84_latitude=48.8566,
        wgs84_longitude=2.3522,
        lambert93_longitude=652469,
        lambert93_latitude=6862035,
        code_insee="17000",
        _save_related=True,
        _fill_optional=True,
    )

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection)}")
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.fill(lieu.nom)
    lieu_form_elements.adresse_input.fill(lieu.adresse_lieu_dit)
    lieu_form_elements.commune_input.fill(lieu.commune)
    lieu_form_elements.code_insee_input.fill(str(lieu.code_insee))
    lieu_form_elements.departement_input.select_option(value=str(lieu.departement.id))
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(lieu.wgs84_latitude))
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(lieu.wgs84_longitude))
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill(str(lieu.lambert93_latitude))
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill(str(lieu.lambert93_longitude))
    lieu_form_elements.save_btn.click()
    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    fd = FicheDetection.objects.get(id=fiche_detection.id)
    lieu_from_db = fd.lieux.first()
    assert fd.lieux.count() == 1
    assert lieu_from_db.nom == lieu.nom
    assert lieu_from_db.adresse_lieu_dit == lieu.adresse_lieu_dit
    assert lieu_from_db.commune == lieu.commune
    assert lieu_from_db.code_insee == str(lieu.code_insee)
    assert lieu_from_db.departement == lieu.departement
    assert lieu_from_db.wgs84_latitude == lieu.wgs84_latitude
    assert lieu_from_db.wgs84_longitude == lieu.wgs84_longitude
    assert lieu_from_db.lambert93_latitude == lieu.lambert93_latitude
    assert lieu_from_db.lambert93_longitude == lieu.lambert93_longitude


@pytest.mark.django_db
def test_add_multiple_lieux(
    live_server,
    page: Page,
    fiche_detection: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que l'ajout de plusieurs lieux est bien enregistré en base de données."""
    lieu_1 = baker.prepare(
        Lieu,
        wgs84_latitude=48.8566,
        wgs84_longitude=2.3522,
        lambert93_longitude=652469,
        lambert93_latitude=6862035,
        code_insee="17000",
        _fill_optional=True,
        _save_related=True,
    )
    lieu_2 = baker.prepare(
        Lieu,
        wgs84_latitude=49.8566,
        wgs84_longitude=3.3522,
        lambert93_longitude=652470,
        lambert93_latitude=6862036,
        code_insee="17001",
        _fill_optional=True,
        _save_related=True,
    )
    lieu_3 = baker.prepare(
        Lieu,
        wgs84_latitude=50.8566,
        wgs84_longitude=4.3522,
        lambert93_longitude=652471,
        lambert93_latitude=6862037,
        code_insee="17002",
        _fill_optional=True,
        _save_related=True,
    )
    lieux = [lieu_1, lieu_2, lieu_3]

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection)}")
    for lieu in lieux:
        form_elements.add_lieu_btn.click()
        lieu_form_elements.nom_input.fill(lieu.nom)
        lieu_form_elements.adresse_input.fill(lieu.adresse_lieu_dit)
        lieu_form_elements.commune_input.fill(lieu.commune)
        lieu_form_elements.code_insee_input.fill(lieu.code_insee)
        lieu_form_elements.departement_input.select_option(value=str(lieu.departement.id))
        lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(lieu.wgs84_latitude))
        lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(lieu.wgs84_longitude))
        lieu_form_elements.coord_gps_lamber93_latitude_input.fill(str(lieu.lambert93_latitude))
        lieu_form_elements.coord_gps_lamber93_longitude_input.fill(str(lieu.lambert93_longitude))
        lieu_form_elements.save_btn.click()

    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    lieu_1_from_db = Lieu.objects.get(nom=lieux[0].nom)
    lieu_2_from_db = Lieu.objects.get(nom=lieux[1].nom)
    lieu_3_from_db = Lieu.objects.get(nom=lieux[2].nom)

    for lieu, lieu_from_db in zip(lieux, [lieu_1_from_db, lieu_2_from_db, lieu_3_from_db]):
        assert lieu_from_db.nom == lieu.nom
        assert lieu_from_db.adresse_lieu_dit == lieu.adresse_lieu_dit
        assert lieu_from_db.commune == lieu.commune
        assert lieu_from_db.code_insee == str(lieu.code_insee)
        assert lieu_from_db.departement == lieu.departement
        assert lieu_from_db.wgs84_latitude == lieu.wgs84_latitude
        assert lieu_from_db.wgs84_longitude == lieu.wgs84_longitude
        assert lieu_from_db.lambert93_latitude == lieu.lambert93_latitude
        assert lieu_from_db.lambert93_longitude == lieu.lambert93_longitude


@pytest.mark.django_db
def test_update_lieu(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que les modifications des descripteurs d'un lieu existant sont bien enregistrées en base de données."""

    dept = baker.make(Departement)
    type_exploitant = baker.make(TypeExploitant)
    position = baker.make(PositionChaineDistribution)
    new_lieu = baker.prepare(
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
        _save_related=True,
    )

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection_with_one_lieu)}")
    page.get_by_role("button", name="Modifier le lieu").click()
    lieu_form_elements.nom_input.fill(new_lieu.nom)
    lieu_form_elements.adresse_input.fill(new_lieu.adresse_lieu_dit)
    lieu_form_elements.commune_input.fill(new_lieu.commune)
    lieu_form_elements.code_insee_input.fill(new_lieu.code_insee)
    lieu_form_elements.departement_input.select_option(value=str(new_lieu.departement.id))
    lieu_form_elements.coord_gps_lamber93_latitude_input.fill(str(new_lieu.lambert93_latitude))
    lieu_form_elements.coord_gps_lamber93_longitude_input.fill(str(new_lieu.lambert93_longitude))
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(new_lieu.wgs84_latitude))
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(new_lieu.wgs84_longitude))
    lieu_form_elements.is_etablissement_checkbox.click()
    lieu_form_elements.nom_etablissement_input.fill(new_lieu.nom_etablissement)
    lieu_form_elements.activite_etablissement_input.fill(new_lieu.activite_etablissement)
    lieu_form_elements.pays_etablissement_input.fill(new_lieu.pays_etablissement)
    lieu_form_elements.raison_sociale_etablissement_input.fill(new_lieu.raison_sociale_etablissement)
    lieu_form_elements.adresse_etablissement_input.fill(new_lieu.adresse_etablissement)
    lieu_form_elements.siret_etablissement_input.fill(new_lieu.siret_etablissement)
    lieu_form_elements.type_etablissement_input.select_option(str(new_lieu.type_exploitant_etablissement.id))
    lieu_form_elements.position_etablissement_input.select_option(
        str(new_lieu.position_chaine_distribution_etablissement.id)
    )
    lieu_form_elements.save_btn.click()
    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    fd = FicheDetection.objects.get(id=fiche_detection_with_one_lieu.id)
    lieu_from_db = fd.lieux.first()
    assert lieu_from_db.nom == new_lieu.nom
    assert lieu_from_db.wgs84_latitude == new_lieu.wgs84_latitude
    assert lieu_from_db.wgs84_longitude == new_lieu.wgs84_longitude
    assert lieu_from_db.lambert93_latitude == new_lieu.lambert93_latitude
    assert lieu_from_db.lambert93_longitude == new_lieu.lambert93_longitude
    assert lieu_from_db.adresse_lieu_dit == new_lieu.adresse_lieu_dit
    assert lieu_from_db.commune == new_lieu.commune
    assert lieu_from_db.code_insee == str(new_lieu.code_insee)
    assert lieu_from_db.departement == new_lieu.departement
    assert lieu_from_db.is_etablissement == new_lieu.is_etablissement
    assert lieu_from_db.nom_etablissement == new_lieu.nom_etablissement
    assert lieu_from_db.activite_etablissement == new_lieu.activite_etablissement
    assert lieu_from_db.pays_etablissement == new_lieu.pays_etablissement
    assert lieu_from_db.raison_sociale_etablissement == new_lieu.raison_sociale_etablissement
    assert lieu_from_db.adresse_etablissement == new_lieu.adresse_etablissement
    assert lieu_from_db.siret_etablissement == new_lieu.siret_etablissement
    assert lieu_from_db.type_exploitant_etablissement == new_lieu.type_exploitant_etablissement
    assert (
        lieu_from_db.position_chaine_distribution_etablissement == new_lieu.position_chaine_distribution_etablissement
    )


@pytest.mark.django_db
def test_update_two_lieux(
    live_server,
    page: Page,
    fiche_detection_with_two_lieux: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que les modifications des descripteurs de plusieurs lieux existants sont bien enregistrées en base de données."""
    new_lieux = baker.prepare(
        Lieu,
        _quantity=2,
        wgs84_latitude=48.8566,
        wgs84_longitude=2.3522,
        _fill_optional=True,
        _save_related=True,
        lambert93_longitude=652469,
        lambert93_latitude=6862035,
        code_insee="17000",
    )

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection_with_two_lieux)}")
    for index, new_lieu in enumerate(new_lieux):
        if index == 0:
            page.get_by_role("button", name="Modifier le lieu").first.click()
        else:
            page.get_by_role("button", name="Modifier le lieu").nth(index).click()
        lieu_form_elements.nom_input.fill(new_lieu.nom)
        lieu_form_elements.adresse_input.fill(new_lieu.adresse_lieu_dit)
        lieu_form_elements.commune_input.fill(new_lieu.commune)
        lieu_form_elements.code_insee_input.fill(new_lieu.code_insee)
        lieu_form_elements.departement_input.select_option(value=str(new_lieu.departement.id))
        lieu_form_elements.coord_gps_lamber93_latitude_input.fill(str(new_lieu.lambert93_latitude))
        lieu_form_elements.coord_gps_lamber93_longitude_input.fill(str(new_lieu.lambert93_longitude))
        lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(new_lieu.wgs84_latitude))
        lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(new_lieu.wgs84_longitude))
        lieu_form_elements.save_btn.click()

    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    fd = FicheDetection.objects.get(id=fiche_detection_with_two_lieux.id)
    lieux_from_db = fd.lieux.all()
    for lieu, new_lieu in zip(lieux_from_db, new_lieux):
        assert lieu.nom == new_lieu.nom
        assert lieu.adresse_lieu_dit == new_lieu.adresse_lieu_dit
        assert lieu.commune == new_lieu.commune
        assert lieu.code_insee == str(new_lieu.code_insee)
        assert lieu.departement == new_lieu.departement
        assert lieu.wgs84_latitude == new_lieu.wgs84_latitude
        assert lieu.wgs84_longitude == new_lieu.wgs84_longitude


@pytest.mark.django_db
def test_delete_lieu(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que la suppression d'un lieu existant est bien enregistrée en base de données.
    Il existe qu'un seul lieu en bd."""
    lieu_id = fiche_detection_with_one_lieu.lieux.first().id
    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection_with_one_lieu)}")
    page.get_by_role("button", name="Supprimer le lieu").first.click()
    page.get_by_role("button", name="Supprimer", exact=True).click()
    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    with pytest.raises(ObjectDoesNotExist):
        Lieu.objects.get(id=lieu_id)


@pytest.mark.django_db
def test_delete_one_lieu_from_set_of_lieux(
    live_server,
    page: Page,
    fiche_detection_with_two_lieux: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que la suppression d'un lieu existant est bien enregistrée en base de données.
    Il existe plusieurs lieux en bd. Valide la suppression du lieu selectionné."""
    # TODO
    pass


@pytest.mark.django_db
def test_delete_multiple_lieux(
    live_server,
    page: Page,
    fiche_detection_with_two_lieux: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que la suppression de plusieurs lieux existants est bien enregistrée en base de données."""
    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection_with_two_lieux)}")
    page.get_by_role("button", name="Supprimer le lieu").first.click()
    page.get_by_role("button", name="Supprimer", exact=True).click()
    page.get_by_role("button", name="Supprimer le lieu").first.click()
    page.get_by_role("button", name="Supprimer", exact=True).click()
    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    fd = FicheDetection.objects.get(id=fiche_detection_with_two_lieux.id)
    assert fd.lieux.count() == 0


@pytest.mark.django_db
def test_add_new_prelevement_non_officiel(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
):
    """Test que l'ajout d'un nouveau prelevement non officiel est bien enregistré en base de données."""
    lieu = baker.make(Lieu, fiche_detection=fiche_detection_with_one_lieu, _fill_optional=True)
    prelevement = baker.prepare(Prelevement, lieu=lieu, _fill_optional=True, _save_related=True)

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection_with_one_lieu)}")
    form_elements.add_prelevement_btn.click()
    prelevement_form_elements.lieu_input.select_option(str(prelevement.lieu.id))
    prelevement_form_elements.structure_input.select_option(str(prelevement.structure_preleveur.id))
    prelevement_form_elements.numero_echantillon_input.fill(prelevement.numero_echantillon)
    prelevement_form_elements.date_prelevement_input.fill(prelevement.date_prelevement.strftime("%Y-%m-%d"))
    prelevement_form_elements.site_inspection_input.select_option(str(prelevement.site_inspection.id))
    prelevement_form_elements.matrice_prelevee_input.select_option(str(prelevement.matrice_prelevee.id))
    prelevement_form_elements.espece_echantillon_input.select_option(str(prelevement.espece_echantillon.id))
    prelevement_form_elements.resultat_input(prelevement.resultat).click()
    prelevement_form_elements.save_btn.click()
    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    prelevement_from_db = Prelevement.objects.get(lieu=lieu)
    assert prelevement_from_db.lieu.id == prelevement.lieu.id
    assert prelevement_from_db.structure_preleveur.id == prelevement.structure_preleveur.id
    assert prelevement_from_db.numero_echantillon == prelevement.numero_echantillon
    assert prelevement_from_db.date_prelevement == prelevement.date_prelevement
    assert prelevement_from_db.site_inspection.id == prelevement.site_inspection.id
    assert prelevement_from_db.matrice_prelevee.id == prelevement.matrice_prelevee.id
    assert prelevement_from_db.espece_echantillon.id == prelevement.espece_echantillon.id
    assert prelevement_from_db.resultat == prelevement.resultat
    assert prelevement_from_db.is_officiel is False
    assert prelevement_from_db.numero_phytopass == ""
    assert prelevement_from_db.laboratoire_agree is None
    assert prelevement_from_db.laboratoire_confirmation_officielle is None


@pytest.mark.django_db
def test_add_new_prelevement_officiel(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
):
    """Test que l'ajout d'un nouveau prelevement non officiel est bien enregistré en base de données."""
    lieu = baker.make(Lieu, fiche_detection=fiche_detection_with_one_lieu, _fill_optional=True)
    prelevement = baker.prepare(Prelevement, lieu=lieu, _fill_optional=True, _save_related=True)

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection_with_one_lieu)}")
    form_elements.add_prelevement_btn.click()
    prelevement_form_elements.lieu_input.select_option(str(prelevement.lieu.id))
    prelevement_form_elements.structure_input.select_option(str(prelevement.structure_preleveur.id))
    prelevement_form_elements.numero_echantillon_input.fill(prelevement.numero_echantillon)
    prelevement_form_elements.date_prelevement_input.fill(prelevement.date_prelevement.strftime("%Y-%m-%d"))
    prelevement_form_elements.site_inspection_input.select_option(str(prelevement.site_inspection.id))
    prelevement_form_elements.matrice_prelevee_input.select_option(str(prelevement.matrice_prelevee.id))
    prelevement_form_elements.espece_echantillon_input.select_option(str(prelevement.espece_echantillon.id))
    prelevement_form_elements.resultat_input(prelevement.resultat).click()
    prelevement_form_elements.prelevement_officiel_checkbox.click()
    prelevement_form_elements.numero_phytopass_input.fill(prelevement.numero_phytopass)
    prelevement_form_elements.laboratoire_agree_input.select_option(str(prelevement.laboratoire_agree.id))
    prelevement_form_elements.laboratoire_confirmation_input.select_option(
        str(prelevement.laboratoire_confirmation_officielle.id)
    )
    prelevement_form_elements.save_btn.click()
    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    prelevement_from_db = Prelevement.objects.get(lieu=lieu)
    assert prelevement_from_db.lieu.id == prelevement.lieu.id
    assert prelevement_from_db.structure_preleveur.id == prelevement.structure_preleveur.id
    assert prelevement_from_db.numero_echantillon == prelevement.numero_echantillon
    assert prelevement_from_db.date_prelevement == prelevement.date_prelevement
    assert prelevement_from_db.site_inspection.id == prelevement.site_inspection.id
    assert prelevement_from_db.matrice_prelevee.id == prelevement.matrice_prelevee.id
    assert prelevement_from_db.espece_echantillon.id == prelevement.espece_echantillon.id
    assert prelevement_from_db.resultat == prelevement.resultat
    assert prelevement_from_db.is_officiel is True
    assert prelevement_from_db.numero_phytopass == prelevement.numero_phytopass
    assert prelevement_from_db.laboratoire_agree.id == prelevement.laboratoire_agree.id
    assert (
        prelevement_from_db.laboratoire_confirmation_officielle.id == prelevement.laboratoire_confirmation_officielle.id
    )


@pytest.mark.django_db
def test_add_multiple_prelevements(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
):
    """Test que l'ajout de plusieurs prelevements lié à un même lieu est bien enregistré en base de données."""
    lieu = baker.make(Lieu, fiche_detection=fiche_detection_with_one_lieu, _fill_optional=True)
    prelevements = baker.prepare(Prelevement, _quantity=3, lieu=lieu, _fill_optional=True, _save_related=True)

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection_with_one_lieu)}")
    for prelevement in prelevements:
        form_elements.add_prelevement_btn.click()
        prelevement_form_elements.lieu_input.select_option(str(prelevement.lieu.id))
        prelevement_form_elements.structure_input.select_option(str(prelevement.structure_preleveur.id))
        prelevement_form_elements.numero_echantillon_input.fill(prelevement.numero_echantillon)
        prelevement_form_elements.date_prelevement_input.fill(prelevement.date_prelevement.strftime("%Y-%m-%d"))
        prelevement_form_elements.site_inspection_input.select_option(str(prelevement.site_inspection.id))
        prelevement_form_elements.matrice_prelevee_input.select_option(str(prelevement.matrice_prelevee.id))
        prelevement_form_elements.espece_echantillon_input.select_option(str(prelevement.espece_echantillon.id))
        prelevement_form_elements.resultat_input(prelevement.resultat).click()
        prelevement_form_elements.save_btn.click()

    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    prelevements_from_db = Prelevement.objects.filter(lieu=lieu)
    for prelevement, prelevement_from_db in zip(prelevements, prelevements_from_db):
        assert prelevement_from_db.lieu.id == prelevement.lieu.id
        assert prelevement_from_db.structure_preleveur.id == prelevement.structure_preleveur.id
        assert prelevement_from_db.numero_echantillon == prelevement.numero_echantillon
        assert prelevement_from_db.date_prelevement == prelevement.date_prelevement
        assert prelevement_from_db.site_inspection.id == prelevement.site_inspection.id
        assert prelevement_from_db.matrice_prelevee.id == prelevement.matrice_prelevee.id
        assert prelevement_from_db.espece_echantillon.id == prelevement.espece_echantillon.id
        assert prelevement_from_db.resultat == prelevement.resultat


@pytest.mark.django_db
def test_update_prelevement(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu_and_one_prelevement: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
):
    """Test que les modifications des descripteurs d'un prelevement existant sont bien enregistrées en base de données."""
    new_lieu = baker.make(Lieu, fiche_detection=fiche_detection_with_one_lieu_and_one_prelevement, _fill_optional=True)
    new_prelevement = baker.prepare(Prelevement, lieu=new_lieu, _fill_optional=True, _save_related=True)

    page.goto(
        f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection_with_one_lieu_and_one_prelevement)}"
    )
    page.locator("ul").filter(has_text="Modifier le prélèvement").get_by_role("button").first.click()
    prelevement_form_elements.lieu_input.select_option(str(new_prelevement.lieu.id))
    prelevement_form_elements.structure_input.select_option(str(new_prelevement.structure_preleveur.id))
    prelevement_form_elements.numero_echantillon_input.fill(new_prelevement.numero_echantillon)
    prelevement_form_elements.date_prelevement_input.fill(new_prelevement.date_prelevement.strftime("%Y-%m-%d"))
    prelevement_form_elements.site_inspection_input.select_option(str(new_prelevement.site_inspection.id))
    prelevement_form_elements.matrice_prelevee_input.select_option(str(new_prelevement.matrice_prelevee.id))
    prelevement_form_elements.espece_echantillon_input.select_option(str(new_prelevement.espece_echantillon.id))
    prelevement_form_elements.resultat_input(new_prelevement.resultat).click()
    prelevement_form_elements.save_btn.click()
    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    prelevement_from_db = Prelevement.objects.get(lieu=new_lieu)
    assert prelevement_from_db.lieu.id == new_prelevement.lieu.id
    assert prelevement_from_db.structure_preleveur.id == new_prelevement.structure_preleveur.id
    assert prelevement_from_db.numero_echantillon == new_prelevement.numero_echantillon
    assert prelevement_from_db.date_prelevement == new_prelevement.date_prelevement
    assert prelevement_from_db.site_inspection.id == new_prelevement.site_inspection.id
    assert prelevement_from_db.matrice_prelevee.id == new_prelevement.matrice_prelevee.id
    assert prelevement_from_db.espece_echantillon.id == new_prelevement.espece_echantillon.id
    assert prelevement_from_db.resultat == new_prelevement.resultat


@pytest.mark.django_db
def test_update_multiple_prelevements(
    live_server,
    page: Page,
    fiche_detection: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
):
    """Test que les modifications des descripteurs de plusieurs prelevements existants sont bien enregistrées en base de données."""
    lieu1, lieu2 = baker.make(Lieu, fiche_detection=fiche_detection, _fill_optional=True, _quantity=2)
    baker.make(Prelevement, lieu=lieu1, _fill_optional=True)
    baker.make(Prelevement, lieu=lieu2, _fill_optional=True)
    new_prelevement_1 = baker.prepare(Prelevement, lieu=lieu2, _fill_optional=True, _save_related=True)
    new_prelevement_2 = baker.prepare(Prelevement, lieu=lieu1, _fill_optional=True, _save_related=True)

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection)}")
    for index, new_prelevement in enumerate([new_prelevement_1, new_prelevement_2]):
        if index == 0:
            page.locator("ul").filter(has_text="Modifier le prélèvement").get_by_role("button").first.click()
        else:
            page.locator("#fiche-detection-form #prelevements").get_by_role("button").nth(3).click()

        prelevement_form_elements.lieu_input.select_option(str(new_prelevement.lieu.id))
        prelevement_form_elements.structure_input.select_option(value=str(new_prelevement.structure_preleveur.id))
        prelevement_form_elements.numero_echantillon_input.fill(new_prelevement.numero_echantillon)
        prelevement_form_elements.date_prelevement_input.fill(new_prelevement.date_prelevement.strftime("%Y-%m-%d"))
        prelevement_form_elements.site_inspection_input.select_option(value=str(new_prelevement.site_inspection.id))
        prelevement_form_elements.matrice_prelevee_input.select_option(value=str(new_prelevement.matrice_prelevee.id))
        prelevement_form_elements.espece_echantillon_input.select_option(
            value=str(new_prelevement.espece_echantillon.id)
        )
        prelevement_form_elements.resultat_input(new_prelevement.resultat).click()
        prelevement_form_elements.save_btn.click()

    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    prelevement_from_db_1 = Prelevement.objects.get(lieu=new_prelevement_1.lieu)
    prelevement_from_db_2 = Prelevement.objects.get(lieu=new_prelevement_2.lieu)
    for prelevement_from_db, new_prelevement in zip(
        [prelevement_from_db_1, prelevement_from_db_2], [new_prelevement_1, new_prelevement_2]
    ):
        assert prelevement_from_db.lieu.id == new_prelevement.lieu.id
        assert prelevement_from_db.structure_preleveur.id == new_prelevement.structure_preleveur.id
        assert prelevement_from_db.numero_echantillon == new_prelevement.numero_echantillon
        assert prelevement_from_db.date_prelevement == new_prelevement.date_prelevement
        assert prelevement_from_db.site_inspection.id == new_prelevement.site_inspection.id
        assert prelevement_from_db.matrice_prelevee.id == new_prelevement.matrice_prelevee.id
        assert prelevement_from_db.espece_echantillon.id == new_prelevement.espece_echantillon.id
        assert prelevement_from_db.resultat == new_prelevement.resultat


@pytest.mark.django_db
def test_delete_prelevement(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu_and_one_prelevement: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
):
    """Test que la suppression d'un prelevement existant est bien enregistrée en base de données."""
    prelevement_id = fiche_detection_with_one_lieu_and_one_prelevement.lieux.first().prelevements.first().id

    page.goto(
        f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection_with_one_lieu_and_one_prelevement)}"
    )
    page.locator("ul").filter(has_text="Supprimer le prélèvement").get_by_role("button").nth(1).click()
    page.locator("#modal-delete-prelevement-confirmation").get_by_role("button", name="Supprimer").click()
    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    with pytest.raises(ObjectDoesNotExist):
        Prelevement.objects.get(id=prelevement_id)


@pytest.mark.django_db
def test_delete_multiple_prelevements(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
):
    """Test que la suppression de plusieurs prelevements existants est bien enregistrée en base de données."""
    prelevement_1, prelevement_2 = baker.make(
        Prelevement, lieu=fiche_detection_with_one_lieu.lieux.first(), _quantity=2
    )

    page.goto(f"{live_server.url}{get_fiche_detection_update_form_url(fiche_detection_with_one_lieu)}")
    # Supprime le premier prélèvement
    page.locator("#fiche-detection-form #prelevements").get_by_role("button").nth(2).click()
    page.locator("#modal-delete-prelevement-confirmation").get_by_role("button", name="Supprimer").click()

    # Supprime le deuxième prélèvement
    page.locator("ul").filter(has_text="Modifier le prélèvement").get_by_role("button").nth(1).click()
    page.locator("#modal-delete-prelevement-confirmation").get_by_role("button", name="Supprimer").click()

    form_elements.save_btn.click()
    page.wait_for_timeout(600)

    with pytest.raises(ObjectDoesNotExist):
        Prelevement.objects.get(id=prelevement_1.id)
        Prelevement.objects.get(id=prelevement_2.id)
