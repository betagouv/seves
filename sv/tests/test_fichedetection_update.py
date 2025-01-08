import pytest
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from model_bakery import baker
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE
from sv.constants import REGIONS, DEPARTEMENTS, STRUCTURE_EXPLOITANT
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements, PrelevementFormDomElements
from ..factories import FicheDetectionFactory, LieuFactory
from ..models import (
    FicheDetection,
    Lieu,
    Prelevement,
    Departement,
    PositionChaineDistribution,
    OrganismeNuisible,
    StructurePreleveuse,
    SiteInspection,
    Laboratoire,
)
from ..models import (
    Region,
)


@pytest.fixture(autouse=True)
def create_fixtures_if_needed(db):
    for nom in REGIONS:
        Region.objects.get_or_create(nom=nom)
    for numero, nom, region_nom in DEPARTEMENTS:
        region = Region.objects.get(nom=region_nom)
        Departement.objects.get_or_create(numero=numero, nom=nom, region=region)


@pytest.fixture
def fiche_detection_with_one_lieu(fiche_detection, lieu_bakery, db):
    lieu = lieu_bakery()
    lieu.fiche_detection = fiche_detection
    lieu.save()
    return fiche_detection


@pytest.fixture
def fiche_detection_with_two_lieux(fiche_detection, db):
    baker.make(Lieu, fiche_detection=fiche_detection, code_insee="65455", _fill_optional=True)
    baker.make(Lieu, fiche_detection=fiche_detection, code_insee="65455", _fill_optional=True)
    return fiche_detection


@pytest.fixture
def fiche_detection_with_one_lieu_and_one_prelevement(fiche_detection_with_one_lieu, db):
    baker.make(
        Prelevement,
        lieu=fiche_detection_with_one_lieu.lieux.get(),
        is_officiel=True,
        _fill_optional=True,
        numero_rapport_inspection="24-123456",
    )
    return fiche_detection_with_one_lieu


def test_page_title(live_server, page: Page):
    fiche = FicheDetectionFactory()
    page.goto(f"{live_server.url}{fiche.get_update_url()}")
    expect(
        page.get_by_role("heading", name=f"Modification de la fiche détection n° {fiche.numero}", exact=True)
    ).to_be_visible()


def test_fiche_detection_update_page_content(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, fiche_detection: FicheDetection
):
    """Test que toutes les données de la fiche de détection sont affichées sur la page de modification de la fiche de détection."""

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")

    # Statut évènement
    expect(form_elements.statut_evenement_input).to_contain_text(fiche_detection.statut_evenement.libelle)
    expect(form_elements.statut_evenement_input).to_have_value(str(fiche_detection.statut_evenement.id))

    # Contexte
    expect(form_elements.contexte_input).to_contain_text(fiche_detection.contexte.nom)
    expect(form_elements.contexte_input).to_have_value(str(fiche_detection.contexte.id))

    # Date 1er signalement
    expect(form_elements.date_1er_signalement_input).to_have_value(str(fiche_detection.date_premier_signalement))

    # Commentaire
    expect(form_elements.commentaire_input).to_have_value(fiche_detection.commentaire)

    # Végétaux infestés
    expect(form_elements.vegetaux_infestes_input).to_have_value(fiche_detection.vegetaux_infestes)

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

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")

    expect(form_elements.statut_evenement_input).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(form_elements.statut_evenement_input).to_have_value("")
    expect(form_elements.contexte_input).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(form_elements.contexte_input).to_have_value("")
    expect(form_elements.date_1er_signalement_input).to_have_value("")
    expect(form_elements.commentaire_input).to_have_value("")
    expect(form_elements.vegetaux_infestes_input).to_have_value("")
    expect(form_elements.mesures_conservatoires_immediates_input).to_have_value("")
    expect(form_elements.mesures_consignation_input).to_have_value("")
    expect(form_elements.mesures_phytosanitaires_input).to_have_value("")
    expect(form_elements.mesures_surveillance_specifique_input).to_have_value("")


@pytest.mark.skip(reason="refacto evenement")
@pytest.mark.django_db
def test_fiche_detection_update_without_lieux_and_prelevement(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    fiche_detection: FicheDetection,
    fiche_detection_bakery,
    mocked_authentification_user,
    choice_js_fill,
):
    """Test que les modifications des informations, objet de l'évènement et mesures de gestion sont bien enregistrées en base de données apès modification."""
    organisme = baker.make(OrganismeNuisible)
    new_fiche_detection = fiche_detection_bakery()
    new_fiche_detection.organisme_nuisible = baker.make(OrganismeNuisible)
    new_fiche_detection.save()

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    form_elements.statut_evenement_input.select_option(str(new_fiche_detection.statut_evenement.id))

    choice_js_fill(page, "#organisme-nuisible .choices__list--single", organisme.libelle_court, organisme.libelle_court)

    form_elements.statut_reglementaire_input.select_option(str(new_fiche_detection.statut_reglementaire.id))
    form_elements.contexte_input.select_option(str(new_fiche_detection.contexte.id))
    form_elements.date_1er_signalement_input.fill(new_fiche_detection.date_premier_signalement.strftime("%Y-%m-%d"))
    form_elements.commentaire_input.fill(new_fiche_detection.commentaire)
    form_elements.vegetaux_infestes_input.fill(new_fiche_detection.vegetaux_infestes)
    form_elements.mesures_conservatoires_immediates_input.fill(new_fiche_detection.mesures_conservatoires_immediates)
    form_elements.mesures_consignation_input.fill(new_fiche_detection.mesures_consignation)
    form_elements.mesures_phytosanitaires_input.fill(new_fiche_detection.mesures_phytosanitaires)
    form_elements.mesures_surveillance_specifique_input.fill(new_fiche_detection.mesures_surveillance_specifique)
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    fiche_detection_updated = FicheDetection.objects.get(id=fiche_detection.id)
    assert (
        fiche_detection_updated.createur == fiche_detection.createur
    )  # le createur ne doit pas changer lors d'une modification
    assert fiche_detection_updated.statut_evenement == new_fiche_detection.statut_evenement
    assert fiche_detection_updated.organisme_nuisible == organisme
    assert fiche_detection_updated.statut_reglementaire == new_fiche_detection.statut_reglementaire
    assert fiche_detection_updated.contexte == new_fiche_detection.contexte
    assert fiche_detection_updated.commentaire == new_fiche_detection.commentaire
    assert fiche_detection_updated.vegetaux_infestes == new_fiche_detection.vegetaux_infestes
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
def test_saving_without_changing_organisme_works(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    fiche_detection_bakery,
    mocked_authentification_user,
):
    organisme = baker.make(OrganismeNuisible)
    new_fiche_detection = fiche_detection_bakery()
    new_fiche_detection.organisme_nuisible = organisme
    new_fiche_detection.save()

    page.goto(f"{live_server.url}{new_fiche_detection.get_update_url()}")
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    new_fiche_detection.refresh_from_db()
    assert new_fiche_detection.organisme_nuisible == organisme


@pytest.mark.django_db
def test_saving_without_changes_does_create_revision(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    fiche_detection_bakery,
    mocked_authentification_user,
):
    fiche = FicheDetectionFactory()
    assert fiche.latest_version is not None
    latest_version = fiche.latest_version

    page.goto(f"{live_server.url}{fiche.get_update_url()}")
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    fiche.refresh_from_db()
    assert latest_version.pk != fiche.latest_version.pk
    assert latest_version.revision.date_created <= fiche.latest_version.revision.date_created


@pytest.mark.django_db
def test_add_new_lieu(
    live_server,
    page: Page,
    fiche_detection: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
    fill_commune,
):
    """Test que l'ajout d'un nouveau lieu est bien enregistré en base de données."""
    lieu = baker.prepare(
        Lieu,
        wgs84_latitude=48.8566,
        wgs84_longitude=2.3522,
        code_insee="17000",
        _save_related=True,
        _fill_optional=True,
    )

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.fill(lieu.nom)
    lieu_form_elements.adresse_input.fill(lieu.adresse_lieu_dit)
    fill_commune(page)
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(lieu.wgs84_latitude))
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(lieu.wgs84_longitude))
    lieu_form_elements.save_btn.click()
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    fd = FicheDetection.objects.get(id=fiche_detection.id)
    lieu_from_db = fd.lieux.first()
    assert fd.lieux.count() == 1
    assert lieu_from_db.nom == lieu.nom
    assert lieu_from_db.adresse_lieu_dit == lieu.adresse_lieu_dit
    assert lieu_from_db.commune == "Lille"
    assert lieu_from_db.code_insee == "59350"
    assert lieu_from_db.departement == Departement.objects.get(nom="Nord")
    assert lieu_from_db.wgs84_latitude == lieu.wgs84_latitude
    assert lieu_from_db.wgs84_longitude == lieu.wgs84_longitude


@pytest.mark.django_db
def test_add_multiple_lieux(
    live_server,
    page: Page,
    fiche_detection: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
    fill_commune,
):
    """Test que l'ajout de plusieurs lieux est bien enregistré en base de données."""
    lieu_1 = baker.prepare(
        Lieu,
        wgs84_latitude=48.8566,
        wgs84_longitude=2.3522,
        code_insee="17000",
        _fill_optional=True,
        _save_related=True,
    )
    lieu_2 = baker.prepare(
        Lieu,
        wgs84_latitude=49.8566,
        wgs84_longitude=3.3522,
        code_insee="17001",
        _fill_optional=True,
        _save_related=True,
    )
    lieu_3 = baker.prepare(
        Lieu,
        wgs84_latitude=50.8566,
        wgs84_longitude=4.3522,
        code_insee="17002",
        _fill_optional=True,
        _save_related=True,
    )
    lieux = [lieu_1, lieu_2, lieu_3]

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    for lieu in lieux:
        form_elements.add_lieu_btn.click()
        lieu_form_elements.nom_input.fill(lieu.nom)
        lieu_form_elements.adresse_input.fill(lieu.adresse_lieu_dit)
        fill_commune(page)
        lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(lieu.wgs84_latitude))
        lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(lieu.wgs84_longitude))
        lieu_form_elements.save_btn.click()

    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    assert Lieu.objects.count() == 3
    lieu_1_from_db = Lieu.objects.get(nom=lieux[0].nom)
    lieu_2_from_db = Lieu.objects.get(nom=lieux[1].nom)
    lieu_3_from_db = Lieu.objects.get(nom=lieux[2].nom)

    for lieu, lieu_from_db in zip(lieux, [lieu_1_from_db, lieu_2_from_db, lieu_3_from_db]):
        assert lieu_from_db.nom == lieu.nom
        assert lieu_from_db.adresse_lieu_dit == lieu.adresse_lieu_dit
        assert lieu_from_db.commune == "Lille"
        assert lieu_from_db.code_insee == "59350"
        assert lieu_from_db.departement == Departement.objects.get(nom="Nord")
        assert lieu_from_db.wgs84_latitude == lieu.wgs84_latitude
        assert lieu_from_db.wgs84_longitude == lieu.wgs84_longitude


@pytest.mark.django_db
def test_update_lieu(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
    fill_commune,
):
    """Test que les modifications des descripteurs d'un lieu existant sont bien enregistrées en base de données."""

    dept = baker.make(Departement)
    site_inspection = baker.make(SiteInspection)
    position = baker.make(PositionChaineDistribution)
    new_lieu = baker.prepare(
        Lieu,
        wgs84_latitude=48.8566,
        wgs84_longitude=2.3522,
        code_insee="17000",
        siret_etablissement="12345678901234",
        departement=dept,
        is_etablissement=True,
        site_inspection=site_inspection,
        position_chaine_distribution_etablissement=position,
        _fill_optional=True,
        _save_related=True,
    )

    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu.get_update_url()}")
    page.get_by_role("button", name="Modifier le lieu").click()
    lieu_form_elements.nom_input.fill(new_lieu.nom)
    lieu_form_elements.adresse_input.fill(new_lieu.adresse_lieu_dit)
    fill_commune(page)
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(new_lieu.wgs84_latitude))
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(new_lieu.wgs84_longitude))
    lieu_form_elements.is_etablissement_checkbox.click(force=True)
    lieu_form_elements.nom_etablissement_input.fill(new_lieu.nom_etablissement)
    lieu_form_elements.activite_etablissement_input.fill(new_lieu.activite_etablissement)
    lieu_form_elements.pays_etablissement_input.fill(new_lieu.pays_etablissement)
    lieu_form_elements.raison_sociale_etablissement_input.fill(new_lieu.raison_sociale_etablissement)
    lieu_form_elements.adresse_etablissement_input.fill(new_lieu.adresse_etablissement)
    lieu_form_elements.siret_etablissement_input.fill(new_lieu.siret_etablissement)
    lieu_form_elements.lieu_site_inspection_input.select_option(str(new_lieu.site_inspection.id))
    lieu_form_elements.position_etablissement_input.select_option(
        str(new_lieu.position_chaine_distribution_etablissement.id)
    )
    lieu_form_elements.save_btn.click()
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    fd = FicheDetection.objects.get(id=fiche_detection_with_one_lieu.id)
    lieu_from_db = fd.lieux.first()
    assert lieu_from_db.nom == new_lieu.nom
    assert lieu_from_db.wgs84_latitude == new_lieu.wgs84_latitude
    assert lieu_from_db.wgs84_longitude == new_lieu.wgs84_longitude
    assert lieu_from_db.adresse_lieu_dit == new_lieu.adresse_lieu_dit
    assert lieu_from_db.commune == "Lille"
    assert lieu_from_db.code_insee == "59350"
    assert lieu_from_db.departement == Departement.objects.get(nom="Nord")
    assert lieu_from_db.is_etablissement == new_lieu.is_etablissement
    assert lieu_from_db.nom_etablissement == new_lieu.nom_etablissement
    assert lieu_from_db.activite_etablissement == new_lieu.activite_etablissement
    assert lieu_from_db.pays_etablissement == new_lieu.pays_etablissement
    assert lieu_from_db.raison_sociale_etablissement == new_lieu.raison_sociale_etablissement
    assert lieu_from_db.adresse_etablissement == new_lieu.adresse_etablissement
    assert lieu_from_db.siret_etablissement == new_lieu.siret_etablissement
    assert lieu_from_db.site_inspection == new_lieu.site_inspection
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
    choice_js_fill,
):
    """Test que les modifications des descripteurs de plusieurs lieux existants sont bien enregistrées en base de données."""
    new_lieux = baker.prepare(
        Lieu,
        _quantity=2,
        wgs84_latitude=48.8566,
        wgs84_longitude=2.3522,
        _fill_optional=True,
        _save_related=True,
        code_insee="17000",
    )

    page.goto(f"{live_server.url}{fiche_detection_with_two_lieux.get_update_url()}")
    for index, new_lieu in enumerate(new_lieux):
        if index == 0:
            page.get_by_role("button", name="Modifier le lieu").first.click()
        else:
            page.get_by_role("button", name="Modifier le lieu").nth(index).click()
        lieu_form_elements.nom_input.fill(new_lieu.nom)
        lieu_form_elements.adresse_input.fill(new_lieu.adresse_lieu_dit)
        if index == 0:
            choice_js_fill(
                page,
                f"#modal-add-lieu-{fiche_detection_with_two_lieux.lieux.first().id} .fr-modal__content .choices__list--single",
                "Lille",
                "Lille (59)",
            )
        else:
            choice_js_fill(
                page,
                f"#modal-add-lieu-{fiche_detection_with_two_lieux.lieux.last().id} .fr-modal__content .choices__list--single",
                "Paris",
                "Paris (75)",
            )
        lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(new_lieu.wgs84_latitude))
        lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(new_lieu.wgs84_longitude))
        lieu_form_elements.save_btn.click()

    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    lieux_from_db = FicheDetection.objects.get(id=fiche_detection_with_two_lieux.id).lieux.all()
    for lieu_from_db, new_lieu in zip(lieux_from_db, new_lieux):
        assert lieu_from_db.nom == new_lieu.nom
        assert lieu_from_db.adresse_lieu_dit == new_lieu.adresse_lieu_dit
        assert lieu_from_db.wgs84_latitude == new_lieu.wgs84_latitude
        assert lieu_from_db.wgs84_longitude == new_lieu.wgs84_longitude

    assert lieux_from_db[0].commune == "Lille"
    assert lieux_from_db[0].code_insee == "59350"
    assert lieux_from_db[0].departement == Departement.objects.get(nom="Nord")
    assert lieux_from_db[1].commune == "Paris"
    assert lieux_from_db[1].code_insee == "75056"
    assert lieux_from_db[1].departement == Departement.objects.get(nom="Paris")


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
    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu.get_update_url()}")
    page.get_by_role("button", name="Supprimer le lieu").first.click()
    page.get_by_role("button", name="Supprimer", exact=True).click()
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    with pytest.raises(ObjectDoesNotExist):
        Lieu.objects.get(id=lieu_id)


@pytest.mark.django_db
def test_delete_lieu_with_prelevement(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu_and_one_prelevement: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    fiche = fiche_detection_with_one_lieu_and_one_prelevement
    lieu = fiche.lieux.first()
    lieu_id = lieu.id
    prelevement_id = lieu.prelevements.first().id

    page.goto(f"{live_server.url}{fiche.get_update_url()}")

    page.locator("ul").filter(has_text="Supprimer le prélèvement").get_by_role("button").nth(1).click()
    page.locator("#modal-delete-prelevement-confirmation").get_by_role("button", name="Supprimer").click()

    page.get_by_role("button", name="Supprimer le lieu").first.click()
    page.get_by_role("button", name="Supprimer", exact=True).click()

    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    with pytest.raises(ObjectDoesNotExist):
        Lieu.objects.get(id=lieu_id)
    with pytest.raises(ObjectDoesNotExist):
        Prelevement.objects.get(id=prelevement_id)


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
    page.goto(f"{live_server.url}{fiche_detection_with_two_lieux.get_update_url()}")
    page.get_by_role("button", name="Supprimer le lieu").first.click()
    page.get_by_role("button", name="Supprimer", exact=True).click()
    page.get_by_role("button", name="Supprimer le lieu").first.click()
    page.get_by_role("button", name="Supprimer", exact=True).click()
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    fd = FicheDetection.objects.get(id=fiche_detection_with_two_lieux.id)
    assert fd.lieux.count() == 0


def test_commune_display_in_card_and_edit_modal(live_server, page: Page):
    fiche_detection = FicheDetectionFactory()
    lieu = LieuFactory(fiche_detection=fiche_detection)

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    expect(page.get_by_text(lieu.commune, exact=True)).to_be_visible()

    page.get_by_role("button", name="Modifier le lieu").click()
    expect(page.get_by_text(f"{lieu.commune} ({lieu.departement.numero})Remove item"))


@pytest.mark.django_db
def test_add_new_prelevement_non_officiel(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    """Test que l'ajout d'un nouveau prelevement non officiel est bien enregistré en base de données."""
    lieu = fiche_detection_with_one_lieu.lieux.first()
    prelevement = baker.prepare(Prelevement, lieu=lieu, resultat="detecte", _fill_optional=True, _save_related=True)

    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu.get_update_url()}")
    form_elements.add_prelevement_btn.click()
    prelevement_form_elements.lieu_input.select_option(str(prelevement.lieu.nom))
    prelevement_form_elements.structure_input.select_option(str(prelevement.structure_preleveuse.id))
    prelevement_form_elements.numero_echantillon_input.fill(prelevement.numero_echantillon)
    prelevement_form_elements.date_prelevement_input.fill(prelevement.date_prelevement.strftime("%Y-%m-%d"))
    prelevement_form_elements.matrice_prelevee_input.select_option(str(prelevement.matrice_prelevee.id))
    choice_js_fill(
        page,
        "#espece-echantillon .choices__list--single",
        prelevement.espece_echantillon.libelle,
        prelevement.espece_echantillon.libelle,
    )
    prelevement_form_elements.type_analyse_input("première intention").click()
    prelevement_form_elements.resultat_input(prelevement.resultat).click()
    prelevement_form_elements.save_btn.click()
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    prelevement_from_db = Prelevement.objects.get(lieu=lieu)
    assert prelevement_from_db.lieu.id == prelevement.lieu.id
    assert prelevement_from_db.structure_preleveuse.id == prelevement.structure_preleveuse.id
    assert prelevement_from_db.numero_echantillon == prelevement.numero_echantillon
    assert prelevement_from_db.date_prelevement == prelevement.date_prelevement
    assert prelevement_from_db.matrice_prelevee.id == prelevement.matrice_prelevee.id
    assert prelevement_from_db.espece_echantillon.id == prelevement.espece_echantillon.id
    assert prelevement_from_db.resultat == prelevement.resultat
    assert prelevement_from_db.is_officiel is False
    assert prelevement_from_db.numero_rapport_inspection == ""
    assert prelevement_from_db.laboratoire is None


@pytest.mark.django_db
def test_add_new_prelevement_with_empty_date(
    live_server,
    page: Page,
    fiche_detection: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
    lieu_form_elements,
):
    StructurePreleveuse.objects.get_or_create(nom="DSF")
    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.fill("Test")
    lieu_form_elements.save_btn.click()
    form_elements.add_prelevement_btn.click()
    prelevement_form_elements.lieu_input.select_option("Test")
    prelevement_form_elements.structure_input.select_option("DSF")
    prelevement_form_elements.resultat_input("detecte").click()
    prelevement_form_elements.type_analyse_input("première intention").click()
    prelevement_form_elements.save_btn.click()
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    prelevement_from_db = Prelevement.objects.get()
    assert prelevement_from_db.date_prelevement is None
    assert prelevement_from_db.resultat == "detecte"


@pytest.mark.django_db
def test_add_new_prelevement_officiel(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    lieu_bakery,
    choice_js_fill,
):
    """Test que l'ajout d'un nouveau prelevement non officiel est bien enregistré en base de données."""
    lieu = lieu_bakery()
    lieu.fiche_detection = fiche_detection_with_one_lieu
    lieu.save()
    prelevement = baker.prepare(
        Prelevement,
        lieu=lieu,
        _fill_optional=True,
        resultat="detecte",
        _save_related=True,
        numero_rapport_inspection="24-123456",
    )

    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu.get_update_url()}")
    form_elements.add_prelevement_btn.click()
    prelevement_form_elements.lieu_input.select_option(str(prelevement.lieu.nom))
    prelevement_form_elements.structure_input.select_option(str(prelevement.structure_preleveuse.id))
    prelevement_form_elements.numero_echantillon_input.fill(prelevement.numero_echantillon)
    prelevement_form_elements.date_prelevement_input.fill(prelevement.date_prelevement.strftime("%Y-%m-%d"))
    prelevement_form_elements.matrice_prelevee_input.select_option(str(prelevement.matrice_prelevee.id))
    choice_js_fill(
        page,
        "#espece-echantillon .choices__list--single",
        prelevement.espece_echantillon.libelle,
        prelevement.espece_echantillon.libelle,
    )
    prelevement_form_elements.type_analyse_input("première intention").click()
    prelevement_form_elements.resultat_input(prelevement.resultat).click()
    prelevement_form_elements.prelevement_officiel_checkbox.click()
    prelevement_form_elements.numero_rapport_inspection_input.fill(prelevement.numero_rapport_inspection)
    prelevement_form_elements.laboratoire_input.select_option(str(prelevement.laboratoire.id))
    prelevement_form_elements.save_btn.click()
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    prelevement_from_db = Prelevement.objects.get(lieu=lieu)
    assert prelevement_from_db.lieu.id == prelevement.lieu.id
    assert prelevement_from_db.structure_preleveuse.id == prelevement.structure_preleveuse.id
    assert prelevement_from_db.numero_echantillon == prelevement.numero_echantillon
    assert prelevement_from_db.date_prelevement == prelevement.date_prelevement
    assert prelevement_from_db.matrice_prelevee.id == prelevement.matrice_prelevee.id
    assert prelevement_from_db.espece_echantillon.id == prelevement.espece_echantillon.id
    assert prelevement_from_db.resultat == prelevement.resultat
    assert prelevement_from_db.is_officiel is True
    assert prelevement_from_db.numero_rapport_inspection == prelevement.numero_rapport_inspection
    assert prelevement_from_db.laboratoire.id == prelevement.laboratoire.id


@pytest.mark.django_db
def test_add_new_prelevement_exploitant_cant_be_officiel(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    lieu_bakery,
    choice_js_fill,
):
    """
    Test qu'un prélèvement :
    - non officiel ne peut pas avoir les champs liés au côté officiel du prélèvement (numéro et laboratoires)
    - qui a pour structure préleveuse l'exploitant ne peut pas être officiel.
    """
    structure_exploitant, _ = StructurePreleveuse.objects.get_or_create(nom=STRUCTURE_EXPLOITANT)
    structure_sral, _ = StructurePreleveuse.objects.get_or_create(nom="SRAL")
    lieu = lieu_bakery()
    lieu.fiche_detection = fiche_detection_with_one_lieu
    lieu.save()
    prelevement = baker.prepare(
        Prelevement, lieu=lieu, _fill_optional=True, resultat=Prelevement.Resultat.DETECTE, _save_related=True
    )

    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu.get_update_url()}")
    form_elements.add_prelevement_btn.click()

    # Fill the form as if it was made by a Structure that can be official
    prelevement_form_elements.lieu_input.select_option(str(prelevement.lieu.nom))
    prelevement_form_elements.structure_input.select_option(str(structure_sral.id))
    prelevement_form_elements.resultat_input(prelevement.resultat).click()
    prelevement_form_elements.prelevement_officiel_checkbox.click()
    prelevement_form_elements.type_analyse_input("première intention").click()
    prelevement_form_elements.laboratoire_input.select_option(str(prelevement.laboratoire.id))

    # Change the structure to exploitant
    prelevement_form_elements.structure_input.select_option(str(structure_exploitant.id))
    expect(prelevement_form_elements.prelevement_officiel_checkbox).to_be_disabled()

    prelevement_form_elements.save_btn.click()
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    prelevement_from_db = Prelevement.objects.get(lieu=lieu)
    assert prelevement_from_db.structure_preleveuse == structure_exploitant
    assert prelevement_from_db.is_officiel is False
    assert prelevement_from_db.numero_rapport_inspection == ""
    assert prelevement_from_db.laboratoire is None


@pytest.mark.django_db
def test_add_multiple_prelevements(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill_from_element,
):
    """Test que l'ajout de plusieurs prelevements lié à un même lieu est bien enregistré en base de données."""
    lieu = baker.make(Lieu, fiche_detection=fiche_detection_with_one_lieu, _fill_optional=True)
    prelevements = baker.prepare(Prelevement, _quantity=3, lieu=lieu, _fill_optional=True, _save_related=True)

    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu.get_update_url()}")
    for prelevement in prelevements:
        form_elements.add_prelevement_btn.click()
        prelevement_form_elements.lieu_input.select_option(str(prelevement.lieu.nom))
        prelevement_form_elements.structure_input.select_option(str(prelevement.structure_preleveuse.id))
        prelevement_form_elements.numero_echantillon_input.fill(prelevement.numero_echantillon)
        prelevement_form_elements.date_prelevement_input.fill(prelevement.date_prelevement.strftime("%Y-%m-%d"))
        prelevement_form_elements.matrice_prelevee_input.select_option(str(prelevement.matrice_prelevee.id))
        element = page.locator(".fr-modal__content").locator("visible=true").locator(".choices__list--single")
        choice_js_fill_from_element(
            page,
            element,
            prelevement.espece_echantillon.libelle,
            prelevement.espece_echantillon.libelle,
        )
        prelevement_form_elements.type_analyse_input("première intention").click()
        prelevement_form_elements.resultat_input(prelevement.resultat).click()
        prelevement_form_elements.save_btn.click()

    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    prelevements_from_db = Prelevement.objects.filter(lieu=lieu)
    for prelevement, prelevement_from_db in zip(prelevements, prelevements_from_db):
        assert prelevement_from_db.lieu.id == prelevement.lieu.id
        assert prelevement_from_db.structure_preleveuse.id == prelevement.structure_preleveuse.id
        assert prelevement_from_db.numero_echantillon == prelevement.numero_echantillon
        assert prelevement_from_db.date_prelevement == prelevement.date_prelevement
        assert prelevement_from_db.matrice_prelevee.id == prelevement.matrice_prelevee.id
        assert prelevement_from_db.espece_echantillon.id == prelevement.espece_echantillon.id
        assert prelevement_from_db.resultat == prelevement.resultat


@pytest.mark.django_db
def test_update_prelevement(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu_and_one_prelevement: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    lieu_bakery,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    """Test que les modifications des descripteurs d'un prelevement existant sont bien enregistrées en base de données."""
    fiche = fiche_detection_with_one_lieu_and_one_prelevement
    new_lieu = lieu_bakery()
    new_lieu.fiche_detection = fiche
    new_lieu.save()
    new_prelevement = baker.prepare(
        Prelevement,
        lieu=new_lieu,
        resultat="detecte",
        _fill_optional=True,
        _save_related=True,
        numero_rapport_inspection="24-123456",
    )

    page.goto(f"{live_server.url}{fiche.get_update_url()}")
    page.locator("ul").filter(has_text="Modifier le prélèvement").get_by_role("button").first.click()
    prelevement_form_elements.lieu_input.select_option(str(new_prelevement.lieu))
    prelevement_form_elements.structure_input.select_option(str(new_prelevement.structure_preleveuse.id))
    prelevement_form_elements.numero_echantillon_input.fill(new_prelevement.numero_echantillon)
    prelevement_form_elements.date_prelevement_input.fill(new_prelevement.date_prelevement.strftime("%Y-%m-%d"))
    prelevement_form_elements.matrice_prelevee_input.select_option(str(new_prelevement.matrice_prelevee.id))
    choice_js_fill(
        page,
        "#espece-echantillon .choices__list--single",
        new_prelevement.espece_echantillon.libelle,
        new_prelevement.espece_echantillon.libelle,
    )
    prelevement_form_elements.resultat_input(new_prelevement.resultat).click()
    prelevement_form_elements.save_btn.click()
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    prelevement_from_db = Prelevement.objects.get(lieu=new_lieu)
    assert prelevement_from_db.lieu.id == new_prelevement.lieu.id
    assert prelevement_from_db.structure_preleveuse.id == new_prelevement.structure_preleveuse.id
    assert prelevement_from_db.numero_echantillon == new_prelevement.numero_echantillon
    assert prelevement_from_db.date_prelevement == new_prelevement.date_prelevement
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
    lieu_bakery,
    choice_js_fill_from_element,
):
    """Test que les modifications des descripteurs de plusieurs prelevements existants sont bien enregistrées en base de données."""
    lieu1, lieu2 = lieu_bakery(), lieu_bakery()
    lieu1.fiche_detection = fiche_detection
    lieu1.save()
    lieu2.fiche_detection = fiche_detection
    lieu2.save()
    baker.make(Prelevement, lieu=lieu1, _fill_optional=True, is_officiel=True, numero_rapport_inspection="24-123456")
    baker.make(Prelevement, lieu=lieu2, _fill_optional=True, is_officiel=True, numero_rapport_inspection="24-123456")
    new_prelevement_1 = baker.prepare(
        Prelevement,
        lieu=lieu1,
        resultat="detecte",
        is_officiel=True,
        _fill_optional=True,
        _save_related=True,
        numero_rapport_inspection="24-123456",
    )
    new_prelevement_2 = baker.prepare(
        Prelevement,
        lieu=lieu2,
        resultat="detecte",
        is_officiel=True,
        _fill_optional=True,
        _save_related=True,
        numero_rapport_inspection="24-123456",
    )

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    for index, new_prelevement in enumerate([new_prelevement_1, new_prelevement_2]):
        page.locator(".prelevement-edit-btn").nth(index).click()
        prelevement_form_elements.lieu_input.select_option(str(new_prelevement.lieu))
        prelevement_form_elements.structure_input.select_option(value=str(new_prelevement.structure_preleveuse.id))
        prelevement_form_elements.numero_echantillon_input.fill(new_prelevement.numero_echantillon)
        prelevement_form_elements.date_prelevement_input.fill(new_prelevement.date_prelevement.strftime("%Y-%m-%d"))
        prelevement_form_elements.matrice_prelevee_input.select_option(value=str(new_prelevement.matrice_prelevee.id))
        espece = prelevement_form_elements.espece_echantillon_choices
        choice_js_fill_from_element(
            page,
            espece,
            new_prelevement.espece_echantillon.libelle,
            new_prelevement.espece_echantillon.libelle,
        )
        prelevement_form_elements.resultat_input(new_prelevement.resultat).click()
        prelevement_form_elements.save_btn.click()

    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    assert Prelevement.objects.count() == 2
    prelevement_from_db_1 = Prelevement.objects.get(lieu=lieu1)
    prelevement_from_db_2 = Prelevement.objects.get(lieu=lieu2)
    for prelevement_from_db, new_prelevement in zip(
        [prelevement_from_db_1, prelevement_from_db_2], [new_prelevement_1, new_prelevement_2]
    ):
        assert prelevement_from_db.lieu.id == new_prelevement.lieu.id
        assert prelevement_from_db.structure_preleveuse.id == new_prelevement.structure_preleveuse.id
        assert prelevement_from_db.numero_echantillon == new_prelevement.numero_echantillon
        assert prelevement_from_db.date_prelevement == new_prelevement.date_prelevement
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

    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu_and_one_prelevement.get_update_url()}")
    page.locator("ul").filter(has_text="Supprimer le prélèvement").get_by_role("button").nth(1).click()
    page.locator("#modal-delete-prelevement-confirmation").get_by_role("button", name="Supprimer").click()
    form_elements.save_update_btn.click()
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
    lieu = fiche_detection_with_one_lieu.lieux.first()
    prelevement_1, prelevement_2 = baker.make(
        Prelevement, lieu=lieu, _quantity=2, is_officiel=True, _fill_optional=True
    )

    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu.get_update_url()}")
    # Supprime le premier prélèvement
    page.locator(".prelevement-delete-btn").first.click()
    page.locator("#modal-delete-prelevement-confirmation").get_by_role("button", name="Supprimer").click()

    # Supprime le deuxième prélèvement
    page.locator(".prelevement-delete-btn").first.click()
    page.locator("#modal-delete-prelevement-confirmation").get_by_role("button", name="Supprimer").click()
    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    assert Prelevement.objects.count() == 0


@pytest.mark.django_db
def test_can_edit_and_save_lieu_with_name_only(
    live_server,
    page: Page,
    fiche_detection_bakery,
    lieu_form_elements,
    form_elements: FicheDetectionFormDomElements,
):
    fiche = fiche_detection_bakery()
    Lieu.objects.create(fiche_detection=fiche, nom="Chez moi")

    page.goto(f"{live_server.url}{fiche.get_update_url()}")
    page.get_by_role("button", name="Modifier le lieu").click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("Chez moi mis à jour")
    lieu_form_elements.save_btn.click()
    form_elements.save_update_btn.click()

    page.wait_for_timeout(600)

    fiche = FicheDetection.objects.get()
    lieu = fiche.lieux.get()
    assert lieu.nom == "Chez moi mis à jour"


def test_cant_pick_inactive_labo_in_prelevement(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu_and_one_prelevement: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    labo = Laboratoire.objects.create(nom="Haunted lab", is_active=False)

    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu_and_one_prelevement.get_update_url()}")

    page.locator("ul").filter(has_text="Modifier le prélèvement").get_by_role("button").first.click()
    assert prelevement_form_elements.laboratoire_input.locator(f'option[value="{labo.pk}"]').count() == 0


@pytest.mark.django_db
def test_can_pick_inactive_labo_in_prelevement_is_old_fiche(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu_and_one_prelevement: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    labo = Laboratoire.objects.create(nom="Haunted lab", is_active=False)
    prelevement = fiche_detection_with_one_lieu_and_one_prelevement.lieux.get().prelevements.get()
    prelevement.laboratoire = labo
    prelevement.save()
    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu_and_one_prelevement.get_update_url()}")
    page.locator("ul").filter(has_text="Modifier le prélèvement").get_by_role("button").first.click()

    assert prelevement_form_elements.laboratoire_input.locator(f'option[value="{labo.pk}"]').count() == 1


@pytest.mark.django_db
def test_cant_pick_inactive_structure_in_prelevement(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu_and_one_prelevement: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    structure = StructurePreleveuse.objects.create(nom="My Structure", is_active=False)
    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu_and_one_prelevement.get_update_url()}")
    page.locator("ul").filter(has_text="Modifier le prélèvement").get_by_role("button").first.click()
    assert prelevement_form_elements.structure_input.locator(f'option[value="{structure.pk}"]').count() == 0


@pytest.mark.django_db
def test_can_pick_inactive_structure_in_prelevement_is_old_fiche(
    live_server,
    page: Page,
    fiche_detection_with_one_lieu_and_one_prelevement: FicheDetection,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    structure = StructurePreleveuse.objects.create(nom="My Structure", is_active=False)
    prelevement = fiche_detection_with_one_lieu_and_one_prelevement.lieux.get().prelevements.get()
    prelevement.structure_preleveuse = structure
    prelevement.save()

    page.goto(f"{live_server.url}{fiche_detection_with_one_lieu_and_one_prelevement.get_update_url()}")
    page.locator("ul").filter(has_text="Modifier le prélèvement").get_by_role("button").first.click()
    assert prelevement_form_elements.structure_input.locator(f'option[value="{structure.pk}"]').count() == 1


@pytest.mark.django_db
def test_fiche_detection_update_as_ac_can_access_rasff_europhyt(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, mocked_authentification_user, fiche_detection
):
    structure = mocked_authentification_user.agent.structure
    structure.niveau1 = AC_STRUCTURE
    structure.save()

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    page.get_by_label("Numéro Europhyt").fill("1" * 8)
    page.get_by_label("Numéro Rasff").fill("2" * 9)

    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    fiche_detection = FicheDetection.objects.get()
    assert fiche_detection.numero_europhyt == "11111111"
    assert fiche_detection.numero_rasff == "222222222"


@pytest.mark.django_db
def test_fiche_detection_update_cant_forge_form_to_edit_rasff_europhyt(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, mocked_authentification_user, fiche_detection
):
    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    page.evaluate("""
            const form = document.querySelector('main form');
            const input1 = document.createElement('input');
            input1.name = 'numero_europhyt';
            input1.value = '11111111';
            form.appendChild(input1);

            const input2 = document.createElement('input');
            input2.name = 'numero_rasff';
            input2.placeholder = '222222222';
            form.appendChild(input2);
        """)

    form_elements.save_update_btn.click()
    page.wait_for_timeout(600)

    fiche_detection = FicheDetection.objects.get()
    assert fiche_detection.numero_europhyt != "11111111"
    assert fiche_detection.numero_rasff != "222222222"
