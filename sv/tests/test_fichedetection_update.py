import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from faker import Faker
from playwright.sync_api import Page, expect
import pytest

from core.constants import DEPARTEMENTS, REGIONS
from core.factories import DepartementFactory
from core.models import Structure
from sv.constants import STRUCTURE_EXPLOITANT, ElementInfesteQuantiteUnite, ElementInfesteType

from ..factories import (
    ElementInfesteFactory,
    EspeceEchantillonFactory,
    EvenementFactory,
    FicheDetectionFactory,
    LaboratoireFactory,
    LieuFactory,
    PositionChaineDistributionFactory,
    PrelevementFactory,
)
from ..models import (
    Departement,
    ElementInfeste,
    Evenement,
    FicheDetection,
    Laboratoire,
    Lieu,
    Prelevement,
    Region,
    StructurePreleveuse,
)
from .generic_tests.test_fichedetection import generic_test_cant_delete_lieu_with_associated_prelevement
from .pages import EvenementUpdatePage
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements, PrelevementFormDomElements


@pytest.fixture(autouse=True)
def create_fixtures_if_needed(db):
    for nom in REGIONS:
        Region.objects.get_or_create(nom=nom)
    for numero, nom, region_nom in DEPARTEMENTS:
        region = Region.objects.get(nom=region_nom)
        Departement.objects.get_or_create(numero=numero, nom=nom, region=region)


def test_page_title(live_server, page: Page):
    fiche = FicheDetectionFactory()
    page.goto(f"{live_server.url}{fiche.get_update_url()}")
    expect(
        page.get_by_role("heading", name=f"Modification de la fiche détection n° {fiche.numero}", exact=True)
    ).to_be_visible()


def test_fiche_detection_update_page_content(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que toutes les données de la fiche de détection sont affichées sur la page de modification de la fiche de détection."""
    fiche_detection = FicheDetectionFactory()
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

    # TODO: ajouter les tests pour les prélèvements


def test_fiche_detection_update_lieu_modal_content(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
    choice_js_fill,
    choice_js_get_values,
):
    fiche_detection = FicheDetectionFactory()
    lieu = LieuFactory(fiche_detection=fiche_detection, is_etablissement=True)
    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")

    # modification du lieu
    lieu_form_elements.edit_form(0)

    expect(lieu_form_elements.nom_label).to_be_visible()
    expect(lieu_form_elements.nom_label).to_contain_text("Nom du lieu")
    expect(lieu_form_elements.nom_input).to_be_visible()
    expect(lieu_form_elements.nom_input).to_have_value(lieu.nom)

    expect(lieu_form_elements.adresse_input).to_have_value(lieu.adresse_lieu_dit)
    expected_value = f"{lieu.adresse_lieu_dit}\nRemove item"
    assert choice_js_get_values(page, '[id^="id_lieux-"][id$="adresse_lieu_dit"]')[0].replace(
        "\n", " "
    ) == expected_value.replace("\n", " ")

    expect(lieu_form_elements.commune_hidden_input).to_have_value(lieu.commune)
    expect(lieu_form_elements.code_insee_hidden_input).to_have_value(lieu.code_insee)
    expect(page.get_by_text(f"{lieu.commune} ({lieu.departement.numero})Remove item")).to_be_visible()

    expect(lieu_form_elements.coord_gps_wgs84_latitude_label).to_be_visible()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_be_visible()
    expect(lieu_form_elements.coord_gps_wgs84_latitude_input).to_have_value(str(lieu.wgs84_latitude))
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_be_visible()
    expect(lieu_form_elements.coord_gps_wgs84_longitude_input).to_have_value(str(lieu.wgs84_longitude))

    expect(lieu_form_elements.is_etablissement_checkbox).to_be_checked()

    expect(lieu_form_elements.siret_etablissement_input).to_have_value(lieu.siret_etablissement)
    expected_value = f"{lieu.siret_etablissement}\nRemove item"
    assert choice_js_get_values(page, '[id^="id_lieux-"][id$="siret_etablissement"]')[0].replace(
        "\n", " "
    ) == expected_value.replace("\n", " ")

    expect(lieu_form_elements.adresse_etablissement_input).to_have_value(lieu.adresse_etablissement)
    expected_value = f"{lieu.adresse_etablissement}\nRemove item"
    assert choice_js_get_values(page, '[id^="id_lieux-"][id$="adresse_etablissement"]')[0].replace(
        "\n", " "
    ) == expected_value.replace("\n", " ")

    expect(lieu_form_elements.pays_etablissement_input).to_be_visible()
    expect(lieu_form_elements.pays_etablissement_input).to_have_value(lieu.pays_etablissement.code)

    expect(lieu_form_elements.code_inupp_etablissement_input).to_be_visible()
    expect(lieu_form_elements.code_inupp_etablissement_input).to_have_value(str(lieu.code_inupp_etablissement))

    expect(lieu_form_elements.position_etablissement_input).to_be_visible()
    expect(lieu_form_elements.position_etablissement_input).to_have_value(
        str(lieu.position_chaine_distribution_etablissement.id)
    )


def test_fiche_detection_update_page_content_with_no_data(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements
):
    """Test que la page de modification de la fiche de détection affiche aucune donnée pour une fiche détection sans données"""
    fiche_detection = FicheDetectionFactory(
        statut_evenement=None,
        contexte=None,
        date_premier_signalement=None,
        commentaire="",
        mesures_conservatoires_immediates="",
        mesures_consignation="",
        mesures_phytosanitaires="",
        mesures_surveillance_specifique="",
    )

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")

    expect(form_elements.statut_evenement_input).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(form_elements.statut_evenement_input).to_have_value("")
    expect(form_elements.contexte_input).to_contain_text(settings.SELECT_EMPTY_CHOICE)
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
    mocked_authentification_user,
    choice_js_fill,
):
    """Test que les modifications des informations, objet de l'évènement et mesures de gestion sont bien enregistrées en base de données apès modification."""
    fiche_detection = FicheDetectionFactory()
    new_fiche_detection = FicheDetectionFactory()

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    form_elements.statut_evenement_input.select_option(str(new_fiche_detection.statut_evenement.id))

    form_elements.contexte_input.select_option(str(new_fiche_detection.contexte.id))
    form_elements.date_1er_signalement_input.fill(new_fiche_detection.date_premier_signalement.strftime("%Y-%m-%d"))
    form_elements.commentaire_input.fill(new_fiche_detection.commentaire)
    form_elements.mesures_conservatoires_immediates_input.fill(new_fiche_detection.mesures_conservatoires_immediates)
    form_elements.mesures_consignation_input.fill(new_fiche_detection.mesures_consignation)
    form_elements.mesures_phytosanitaires_input.fill(new_fiche_detection.mesures_phytosanitaires)
    form_elements.mesures_surveillance_specifique_input.fill(new_fiche_detection.mesures_surveillance_specifique)
    evenement_page.save()

    fiche_detection_updated = FicheDetection.objects.get(id=fiche_detection.id)
    assert (
        fiche_detection_updated.createur == fiche_detection.createur
    )  # le createur ne doit pas changer lors d'une modification
    assert fiche_detection_updated.statut_evenement == new_fiche_detection.statut_evenement
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
def test_saving_without_changes_does_create_revision(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    mocked_authentification_user,
):
    fiche = FicheDetectionFactory()
    assert fiche.latest_version is not None
    latest_version = fiche.latest_version

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche)
    evenement_page.save()

    fiche.refresh_from_db()
    del fiche.latest_version
    assert latest_version.pk != fiche.latest_version.pk
    assert latest_version.revision.date_created <= fiche.latest_version.revision.date_created


@pytest.mark.django_db
def test_add_new_lieu(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que l'ajout d'un nouveau lieu est bien enregistré en base de données."""
    fiche_detection = FicheDetectionFactory()
    lieu = LieuFactory.build(code_insee="17000")
    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    lieu_form_elements.open_new_form()
    lieu_form_elements.nom_input.fill(lieu.nom)
    lieu_form_elements.force_lieu_address(lieu.adresse_lieu_dit)
    lieu_form_elements.force_commune()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(lieu.wgs84_latitude))
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(lieu.wgs84_longitude))
    lieu_form_elements.lieu_site_inspection_input.select_option("INCONNU")
    lieu_form_elements.close_with(action="save")
    evenement_page.save()

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
    assert lieu_from_db.get_site_inspection_display() == "Inconnu - préciser dans les commentaires"


@pytest.mark.django_db
def test_add_multiple_lieux(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que l'ajout de plusieurs lieux est bien enregistré en base de données."""
    fiche_detection = FicheDetectionFactory()
    lieu_1 = LieuFactory.build(code_insee="17000")
    lieu_2 = LieuFactory.build(code_insee="17001")
    lieu_3 = LieuFactory.build(code_insee="17002")
    lieux = [lieu_1, lieu_2, lieu_3]

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    for lieu in lieux:
        lieu_form_elements.open_new_form()
        lieu_form_elements.nom_input.fill(lieu.nom)
        lieu_form_elements.lieu_site_inspection_input.select_option("INCONNU")
        lieu_form_elements.force_lieu_address(lieu.adresse_lieu_dit)
        lieu_form_elements.force_commune()
        lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(lieu.wgs84_latitude))
        lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(lieu.wgs84_longitude))
        lieu_form_elements.close_with(action="save")

    evenement_page.save()

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
        assert lieu_from_db.get_site_inspection_display() == "Inconnu - préciser dans les commentaires"


@pytest.mark.django_db
def test_update_lieu(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que les modifications des descripteurs d'un lieu existant sont bien enregistrées en base de données."""
    fiche_detection = FicheDetectionFactory(with_lieu=True)
    dept = DepartementFactory()
    position = PositionChaineDistributionFactory()
    new_lieu = LieuFactory.build(
        departement=dept,
        is_etablissement=True,
        position_chaine_distribution_etablissement=position,
    )

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    lieu_form_elements.edit_form(0)
    expect(lieu_form_elements.map_canvas).to_be_visible()
    lieu_form_elements.nom_input.fill(new_lieu.nom)
    lieu_form_elements.force_lieu_address(new_lieu.adresse_lieu_dit)
    lieu_form_elements.force_commune()
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(new_lieu.wgs84_latitude))
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(new_lieu.wgs84_longitude))
    if new_lieu.is_etablissement:
        if not lieu_form_elements.is_etablissement_checkbox.is_checked():
            lieu_form_elements.is_etablissement_checkbox.click()
        lieu_form_elements.activite_etablissement_input.fill(new_lieu.activite_etablissement)
        lieu_form_elements.pays_etablissement_input.select_option(new_lieu.pays_etablissement.code)
        lieu_form_elements.raison_sociale_etablissement_input.fill(new_lieu.raison_sociale_etablissement)
        lieu_form_elements.force_etablissement_address(new_lieu.adresse_etablissement)
        lieu_form_elements.force_siret_etablissement(new_lieu.siret_etablissement)
        lieu_form_elements.lieu_site_inspection_input.select_option(str(new_lieu.site_inspection))
        lieu_form_elements.position_etablissement_input.select_option(
            str(new_lieu.position_chaine_distribution_etablissement.id)
        )
    lieu_form_elements.close_with(action="save")
    evenement_page.save()

    fd = FicheDetection.objects.get(id=fiche_detection.id)
    lieu_from_db = fd.lieux.first()
    assert lieu_from_db.nom == new_lieu.nom
    assert lieu_from_db.wgs84_latitude == new_lieu.wgs84_latitude
    assert lieu_from_db.wgs84_longitude == new_lieu.wgs84_longitude
    assert lieu_from_db.adresse_lieu_dit == new_lieu.adresse_lieu_dit
    assert lieu_from_db.commune == "Lille"
    assert lieu_from_db.code_insee == "59350"
    assert lieu_from_db.departement == Departement.objects.get(nom="Nord")
    assert lieu_from_db.is_etablissement == new_lieu.is_etablissement
    assert lieu_from_db.activite_etablissement == new_lieu.activite_etablissement
    assert lieu_from_db.pays_etablissement == new_lieu.pays_etablissement
    assert lieu_from_db.raison_sociale_etablissement == new_lieu.raison_sociale_etablissement
    assert lieu_from_db.adresse_etablissement == new_lieu.adresse_etablissement.replace("\n", " ")
    assert lieu_from_db.siret_etablissement == new_lieu.siret_etablissement
    assert lieu_from_db.site_inspection == new_lieu.site_inspection
    assert (
        lieu_from_db.position_chaine_distribution_etablissement == new_lieu.position_chaine_distribution_etablissement
    )


@pytest.mark.django_db
def test_update_two_lieux(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
    choice_js_fill,
):
    """Test que les modifications des descripteurs de plusieurs lieux existants sont bien enregistrées en base de données."""
    fiche_detection = FicheDetectionFactory(with_lieu=True)
    LieuFactory(fiche_detection=fiche_detection)
    new_lieux = LieuFactory.build_batch(2, code_insee="17000")

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    for index, new_lieu in enumerate(new_lieux):
        if index == 0:
            page.get_by_role("button", name="Modifier").first.click()
        else:
            page.get_by_role("button", name="Modifier").nth(index).click()
        lieu_form_elements.nom_input.fill(new_lieu.nom)
        lieu_form_elements.force_lieu_address(new_lieu.adresse_lieu_dit)
        if index == 0:
            lieu_form_elements.force_commune()
        else:
            response_body = [
                {
                    "codesPostaux": [
                        "75001",
                        "75002",
                        "75003",
                        "75004",
                        "75005",
                        "75006",
                        "75007",
                        "75008",
                        "75009",
                        "75010",
                        "75011",
                        "75012",
                        "75013",
                        "75014",
                        "75015",
                        "75016",
                        "75017",
                        "75018",
                        "75019",
                        "75020",
                        "75116",
                    ],
                    "nom": "Paris",
                    "code": "75056",
                    "_score": 9.535435286815508,
                    "departement": {"code": "75", "nom": "Paris"},
                }
            ]
            lieu_form_elements.force_commune(
                {
                    "search_text": "Paris",
                    "option_name": f"Paris ({response_body[0]['codesPostaux'][0]})",
                    "response_body": json.dumps(response_body),
                }
            )
        lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(new_lieu.wgs84_latitude))
        lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(new_lieu.wgs84_longitude))
        lieu_form_elements.close_with(action="save")

    evenement_page.save()

    lieux_from_db = FicheDetection.objects.get(id=fiche_detection.id).lieux.all()
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
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que la suppression d'un lieu existant est bien enregistrée en base de données.
    Il existe qu'un seul lieu en bd."""
    fiche_detection = FicheDetectionFactory(with_lieu=True)
    lieu_id = fiche_detection.lieux.first().id
    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)
    lieu_form_elements.remove_card(by_idx=0)
    evenement_page.save()

    with pytest.raises(ObjectDoesNotExist):
        Lieu.objects.get(id=lieu_id)


@pytest.mark.django_db
def test_delete_lieu_with_prelevement(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    fiche = FicheDetectionFactory(with_prelevement=True)
    lieu = fiche.lieux.first()
    lieu_id = lieu.id
    prelevement_id = lieu.prelevements.first().id

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche)

    page.get_by_test_id("prelevement-delete-btn").click()
    page.get_by_test_id("submit-delete").locator("visible=true").click()

    lieu_form_elements.remove_card(by_idx=0)

    evenement_page.save()

    with pytest.raises(ObjectDoesNotExist):
        Lieu.objects.get(id=lieu_id)
    with pytest.raises(ObjectDoesNotExist):
        Prelevement.objects.get(id=prelevement_id)


@pytest.mark.django_db
def test_delete_one_lieu_from_set_of_lieux(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que la suppression d'un lieu existant est bien enregistrée en base de données.
    Il existe plusieurs lieux en bd. Valide la suppression du lieu selectionné."""
    fiche_detection = FicheDetectionFactory(with_lieu=3)
    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    lieux_count = Lieu.objects.count()
    lieu_id = lieu_form_elements.dialogs.nth(1).get_by_test_id("lieu-pk").get_attribute("value")
    lieu_form_elements.remove_card(by_idx=1)
    evenement_page.save()

    with pytest.raises(ObjectDoesNotExist):
        Lieu.objects.get(id=lieu_id)

    assert Lieu.objects.count() == lieux_count - 1


@pytest.mark.django_db
def test_delete_multiple_lieux(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    """Test que la suppression de plusieurs lieux existants est bien enregistrée en base de données."""
    fiche_detection = FicheDetectionFactory(with_lieu=3)

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)
    while lieu_form_elements.elements_cards.count() > 0:
        lieu_form_elements.remove_card(by_idx=0)
    evenement_page.save()

    fd = FicheDetection.objects.get(id=fiche_detection.id)
    assert fd.lieux.count() == 0


def test_cant_delete_lieu_with_associated_prelevement(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    fiche_detection = FicheDetectionFactory(with_lieu=True, with_prelevement=True)
    prelevement = PrelevementFactory(lieu__fiche_detection=fiche_detection)
    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    generic_test_cant_delete_lieu_with_associated_prelevement(prelevement, evenement_page)


def test_commune_display_in_card_and_edit_modal(live_server, page: Page):
    fiche_detection = FicheDetectionFactory()
    lieu = LieuFactory(fiche_detection=fiche_detection)

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)
    lieu_form_elements = LieuFormDomElements(page)
    expect(lieu_form_elements.elements_cards.nth(0)).to_contain_text(f"{lieu.commune}")

    lieu_form_elements.edit_form(0)
    expect(lieu_form_elements.opened_dialog).to_contain_text(f"{lieu.commune}")


@pytest.mark.django_db
def test_add_new_prelevement_non_officiel(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    """Test que l'ajout d'un nouveau prelevement non officiel est bien enregistré en base de données."""
    lieu = LieuFactory()
    prelevement = PrelevementFactory.build_with_some_related_objects_saved(lieu=lieu, is_officiel=False)

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(lieu.fiche_detection)

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
    prelevement_form_elements.date_rapport_analyse_input.fill(prelevement.date_rapport_analyse.strftime("%Y-%m-%d"))
    prelevement_form_elements.save_btn.click()
    evenement_page.save()

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
    assert prelevement_from_db.date_rapport_analyse == prelevement.date_rapport_analyse


@pytest.mark.django_db
def test_add_new_prelevement_officiel(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    lieu = LieuFactory()
    prelevement = PrelevementFactory.build_with_some_related_objects_saved(
        lieu=lieu, is_officiel=True, type_analyse=Prelevement.TypeAnalyse.CONFIRMATION
    )

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(lieu.fiche_detection)

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
    prelevement_form_elements.date_rapport_analyse_input.fill(prelevement.date_rapport_analyse.strftime("%Y-%m-%d"))
    prelevement_form_elements.save_btn.click()
    evenement_page.save()

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
    assert prelevement_from_db.date_rapport_analyse == prelevement.date_rapport_analyse


@pytest.mark.django_db
def test_add_new_prelevement_exploitant_cant_be_officiel(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    """
    Test qu'un prélèvement :
    - non officiel ne peut pas avoir les champs liés au côté officiel du prélèvement (numéro et laboratoires)
    - qui a pour structure préleveuse l'exploitant ne peut pas être officiel.
    """
    structure_exploitant, _ = StructurePreleveuse.objects.get_or_create(nom=STRUCTURE_EXPLOITANT)
    structure_sral, _ = StructurePreleveuse.objects.get_or_create(nom="SRAL")
    lieu = LieuFactory()
    prelevement = PrelevementFactory.build(lieu=lieu, is_officiel=False)

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(lieu.fiche_detection)

    form_elements.add_prelevement_btn.click()

    # Fill the form as if it was made by a Structure that can be official
    prelevement_form_elements.lieu_input.select_option(str(prelevement.lieu.nom))
    prelevement_form_elements.structure_input.select_option(str(structure_sral.id))
    prelevement_form_elements.resultat_input(prelevement.resultat).click()
    prelevement_form_elements.prelevement_officiel_checkbox.click()
    prelevement_form_elements.date_prelevement_input.fill("2021-01-01")
    prelevement_form_elements.type_analyse_input("première intention").click()
    prelevement_form_elements.laboratoire_input.select_option(str(prelevement.laboratoire.id))

    # Change the structure to exploitant
    prelevement_form_elements.structure_input.select_option(str(structure_exploitant.id))
    expect(prelevement_form_elements.prelevement_officiel_checkbox).to_be_disabled()

    prelevement_form_elements.save_btn.click()
    evenement_page.save()

    prelevement_from_db = Prelevement.objects.get(lieu=lieu)
    assert prelevement_from_db.structure_preleveuse == structure_exploitant
    assert prelevement_from_db.is_officiel is False
    assert prelevement_from_db.numero_rapport_inspection == ""
    assert prelevement_from_db.laboratoire is None


@pytest.mark.django_db
def test_add_multiple_prelevements(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill_from_element,
):
    """Test que l'ajout de plusieurs prelevements lié à un même lieu est bien enregistré en base de données."""
    fiche_detection = FicheDetectionFactory(with_lieu=True)
    lieu = LieuFactory(fiche_detection=fiche_detection)
    prelevement_1 = PrelevementFactory.build_with_some_related_objects_saved(lieu=lieu)
    prelevement_2 = PrelevementFactory.build_with_some_related_objects_saved(lieu=lieu)
    prelevement_3 = PrelevementFactory.build_with_some_related_objects_saved(lieu=lieu)
    prelevements = [prelevement_1, prelevement_2, prelevement_3]

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

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
        prelevement_form_elements.date_rapport_analyse_input.fill(prelevement.date_rapport_analyse.strftime("%Y-%m-%d"))
        prelevement_form_elements.save_btn.click()

    evenement_page.save()

    prelevements_from_db = Prelevement.objects.filter(lieu=lieu)
    for prelevement, prelevement_from_db in zip(prelevements, prelevements_from_db):
        assert prelevement_from_db.lieu.id == prelevement.lieu.id
        assert prelevement_from_db.structure_preleveuse.id == prelevement.structure_preleveuse.id
        assert prelevement_from_db.numero_echantillon == prelevement.numero_echantillon
        assert prelevement_from_db.date_prelevement == prelevement.date_prelevement
        assert prelevement_from_db.matrice_prelevee.id == prelevement.matrice_prelevee.id
        assert prelevement_from_db.espece_echantillon.id == prelevement.espece_echantillon.id
        assert prelevement_from_db.resultat == prelevement.resultat
        assert prelevement_from_db.date_rapport_analyse == prelevement.date_rapport_analyse


@pytest.mark.django_db
def test_update_prelevement(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    """Test que les modifications des descripteurs d'un prelevement existant sont bien enregistrées en base de données."""
    prelevement = PrelevementFactory()
    new_lieu = LieuFactory(fiche_detection=prelevement.lieu.fiche_detection)
    new_prelevement = PrelevementFactory.build_with_some_related_objects_saved(lieu=new_lieu, is_officiel=False)

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(new_lieu.fiche_detection)

    page.get_by_test_id("prelevement-update-btn").first.click()
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
    prelevement_form_elements.date_rapport_analyse_input.fill(new_prelevement.date_rapport_analyse.strftime("%Y-%m-%d"))
    prelevement_form_elements.save_btn.click()
    page.wait_for_timeout(600)
    evenement_page.save()

    prelevement_from_db = Prelevement.objects.get(lieu=new_lieu)
    assert prelevement_from_db.lieu.id == new_prelevement.lieu.id
    assert prelevement_from_db.structure_preleveuse.id == new_prelevement.structure_preleveuse.id
    assert prelevement_from_db.numero_echantillon == new_prelevement.numero_echantillon
    assert prelevement_from_db.date_prelevement == new_prelevement.date_prelevement
    assert prelevement_from_db.matrice_prelevee.id == new_prelevement.matrice_prelevee.id
    assert prelevement_from_db.espece_echantillon.id == new_prelevement.espece_echantillon.id
    assert prelevement_from_db.resultat == new_prelevement.resultat
    assert prelevement_from_db.date_rapport_analyse == new_prelevement.date_rapport_analyse


@pytest.mark.django_db
def test_update_multiple_prelevements(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill_from_element,
):
    """Test que les modifications des descripteurs de plusieurs prelevements existants sont bien enregistrées en base de données."""
    fiche_detection = FicheDetectionFactory()
    lieu1, lieu2 = LieuFactory.create_batch(2, fiche_detection=fiche_detection)
    PrelevementFactory(lieu=lieu1, is_officiel=True)
    PrelevementFactory(lieu=lieu2, is_officiel=True)
    new_prelevement_1 = PrelevementFactory.build_with_some_related_objects_saved(lieu=lieu1, is_officiel=False)
    new_prelevement_2 = PrelevementFactory.build_with_some_related_objects_saved(lieu=lieu2, is_officiel=False)

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    for index, new_prelevement in enumerate([new_prelevement_1, new_prelevement_2]):
        expect(
            page.locator("[id*='modal-add-edit-prelevement'] .fr-modal__body").locator("visible=true")
        ).to_have_count(0)
        page.get_by_test_id("prelevement-update-btn").nth(index).click()
        expect(
            page.locator("[id*='modal-add-edit-prelevement'] .fr-modal__body").locator("visible=true")
        ).to_have_count(1)
        prelevement_form_elements.numero_rapport_inspection_input.fill(new_prelevement.numero_rapport_inspection)
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
        prelevement_form_elements.date_rapport_analyse_input.fill(
            new_prelevement.date_rapport_analyse.strftime("%Y-%m-%d")
        )
        prelevement_form_elements.save_btn.click()
        expect(
            page.locator("[id*='modal-add-edit-prelevement'] .fr-modal__body").locator("visible=true")
        ).to_have_count(0)

    evenement_page.save()

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
        assert prelevement_from_db.date_rapport_analyse == new_prelevement.date_rapport_analyse


@pytest.mark.django_db
def test_delete_prelevement(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que la suppression d'un prelevement existant est bien enregistrée en base de données."""
    prelevement = PrelevementFactory()

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(prelevement.lieu.fiche_detection)

    page.get_by_test_id("prelevement-delete-btn").click()
    page.get_by_test_id("submit-delete").locator("visible=true").click()
    evenement_page.save()

    with pytest.raises(ObjectDoesNotExist):
        Prelevement.objects.get(id=prelevement.id)


@pytest.mark.django_db
def test_delete_multiple_prelevements(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que la suppression de plusieurs prelevements existants est bien enregistrée en base de données."""
    lieu = LieuFactory()
    PrelevementFactory.create_batch(2, lieu=lieu)

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(lieu.fiche_detection)
    page.goto(f"{live_server.url}{lieu.fiche_detection.get_update_url()}")
    # Supprime le premier prélèvement
    page.get_by_test_id("prelevement-delete-btn").first.click()
    page.get_by_test_id("submit-delete").locator("visible=true").click()

    # Supprime le deuxième prélèvement
    page.get_by_test_id("prelevement-delete-btn").first.click()
    page.get_by_test_id("submit-delete").locator("visible=true").click()
    evenement_page.save()

    assert Prelevement.objects.count() == 0


@pytest.mark.django_db
def test_can_edit_and_save_lieu_with_name_only(
    live_server,
    page: Page,
    lieu_form_elements,
    form_elements: FicheDetectionFormDomElements,
):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, nom="Chez moi")

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche)

    lieu_form_elements.edit_form(0)
    lieu_form_elements.nom_input.fill("Chez moi mis à jour")
    lieu_form_elements.close_with(action="save")
    evenement_page.save()

    fiche = FicheDetection.objects.get()
    lieu = fiche.lieux.get()
    assert lieu.nom == "Chez moi mis à jour"


def test_cant_pick_inactive_labo_in_prelevement(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    fiche_detection = FicheDetectionFactory(with_prelevement=True)
    labo = Laboratoire.objects.create(nom="Haunted lab", is_active=False)

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")

    page.get_by_test_id("prelevement-update-btn").first.click()
    assert prelevement_form_elements.laboratoire_input.locator(f'option[value="{labo.pk}"]').count() == 0


@pytest.mark.django_db
def test_can_pick_inactive_labo_in_prelevement_is_old_fiche(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    fiche_detection = FicheDetectionFactory(evenement=EvenementFactory())
    lieu = LieuFactory(fiche_detection=fiche_detection)
    labo = Laboratoire.objects.create(nom="Haunted lab", is_active=False)
    PrelevementFactory(lieu=lieu, laboratoire=labo)

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    form_elements.commentaire_input.fill("AAA")
    page.get_by_test_id("prelevement-update-btn").first.click()
    assert prelevement_form_elements.laboratoire_input.locator(f'option[value="{labo.pk}"]').count() == 1
    prelevement_form_elements.save_btn.click()
    evenement_page.save()

    fiche_detection.refresh_from_db()
    assert fiche_detection.commentaire == "AAA"


@pytest.mark.django_db
def test_cant_pick_inactive_structure_in_prelevement(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    fiche_detection = FicheDetectionFactory(with_prelevement=True)
    structure = StructurePreleveuse.objects.create(nom="My Structure", is_active=False)
    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    page.get_by_test_id("prelevement-update-btn").first.click()
    assert prelevement_form_elements.structure_input.locator(f'option[value="{structure.pk}"]').count() == 0


@pytest.mark.django_db
def test_can_pick_inactive_structure_in_prelevement_is_old_fiche(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    fiche_detection = FicheDetectionFactory(evenement=EvenementFactory())
    lieu = LieuFactory(fiche_detection=fiche_detection)
    structure = StructurePreleveuse.objects.create(nom="My Structure", is_active=False)
    PrelevementFactory(lieu=lieu, structure_preleveuse=structure)

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    form_elements.commentaire_input.fill("AAA")
    page.get_by_test_id("prelevement-update-btn").first.click()
    assert prelevement_form_elements.structure_input.locator(f'option[value="{structure.pk}"]').count() == 1
    prelevement_form_elements.save_btn.click()
    evenement_page.save()

    fiche_detection.refresh_from_db()
    assert fiche_detection.commentaire == "AAA"


@pytest.mark.django_db
def test_laboratoire_disable_in_prelevement_confirmation(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
):
    """Test que les laboratoires non officiels sont désactivés quand le type d'analyse est confirmation"""
    LaboratoireFactory.create_batch(3)
    LaboratoireFactory.create_batch(3, confirmation_officielle=True)
    fiche_detection = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche_detection)

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    form_elements.add_prelevement_btn.click()

    prelevement_form_elements.type_analyse_input("confirmation").click()

    # Vérifier le statut disabled/enabled pour tous les laboratoires
    labos_officiels = Laboratoire.objects.filter(confirmation_officielle=True)
    labos_non_officiels = Laboratoire.objects.filter(confirmation_officielle=False)

    for labo in labos_non_officiels:
        expect(prelevement_form_elements.laboratoire_input.locator(f'option[value="{labo.pk}"]')).to_be_disabled()

    for labo in labos_officiels:
        expect(prelevement_form_elements.laboratoire_input.locator(f'option[value="{labo.pk}"]')).not_to_be_disabled()


@pytest.mark.django_db
def test_laboratoire_enable_for_analyse_premiere_intention(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
):
    """Test que tous les laboratoires sont actifs quand le type d'analyse est première intention"""
    LaboratoireFactory.create_batch(3)
    LaboratoireFactory.create_batch(3, confirmation_officielle=True)
    fiche_detection = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche_detection)

    page.goto(f"{live_server.url}{fiche_detection.get_update_url()}")
    form_elements.add_prelevement_btn.click()

    prelevement_form_elements.type_analyse_input("première intention").click()

    # Vérifier qu'aucun labo n'est désactivé
    laboratoires = Laboratoire.objects.all()
    for labo in laboratoires:
        expect(prelevement_form_elements.laboratoire_input.locator(f'option[value="{labo.pk}"]')).not_to_have_attribute(
            "disabled", ""
        )


def test_update_fichedetection_adds_agent_and_structure_contacts(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, mocked_authentification_user
):
    """Test que la modification d'une fiche détection ajoute l'agent et sa structure comme contacts"""
    fiche = FicheDetectionFactory()

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche)

    form_elements.commentaire_input.fill("Nouveau commentaire")
    evenement_page.save()

    fiche.refresh_from_db()
    assert fiche.commentaire == "Nouveau commentaire"
    assert fiche.evenement.contacts.filter(agent=mocked_authentification_user.agent).exists()
    assert fiche.evenement.contacts.filter(structure=mocked_authentification_user.agent.structure).exists()


def test_update_fichedetection_multiple_times_adds_contacts_once(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, mocked_authentification_user
):
    """Test que plusieurs modifications d'une fiche détection n'ajoutent qu'une fois les contacts"""
    fiche = FicheDetectionFactory()

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche)

    form_elements.commentaire_input.fill("Première modification")
    evenement_page.save()

    page.goto(f"{live_server.url}{fiche.get_update_url()}")
    form_elements.commentaire_input.fill("Seconde modification")
    evenement_page.save()

    fiche.refresh_from_db()
    assert fiche.commentaire == "Seconde modification"
    assert fiche.evenement.contacts.filter(agent=mocked_authentification_user.agent).count() == 1
    assert fiche.evenement.contacts.filter(structure=mocked_authentification_user.agent.structure).count() == 1


@pytest.mark.django_db
def test_fiche_detection_update_has_locking_protection(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    mocked_authentification_user,
):
    fiche = FicheDetectionFactory(commentaire="AAA")
    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche)
    page.get_by_label("Commentaire").fill("BBB")

    fiche.commentaire = "CCC"
    fiche.save()

    locking_text = (
        "Vos modifications n'ont pas été enregistrées. Un autre utilisateur a modifié cet objet. "
        "Fermer cette modale pour charger la dernière version."
    )
    expect(page.locator("body")).not_to_contain_text(locking_text)
    evenement_page.save_button.click()
    expect(page.get_by_text(locking_text)).to_be_visible()

    with page.expect_event("framenavigated"):
        page.keyboard.press("Escape")
    expect(page.get_by_text(locking_text)).not_to_be_visible()

    fiche.refresh_from_db()
    assert fiche.commentaire == "CCC"


def test_cant_forge_update_of_detection_i_cant_see(client):
    prelevements = {}
    lieux = {}
    for i in range(0, 20):
        prelevements.update(
            {
                f"prelevements-{i}-numero_rapport_inspection": [""],
                f"prelevements-{i}-laboratoire": [""],
                f"prelevements-{i}-numero_echantillon": [""],
                f"prelevements-{i}-structure_preleveuse": [""],
                f"prelevements-{i}-date_prelevement": [""],
                f"prelevements-{i}-matrice_prelevee": [""],
            }
        )
    for i in range(0, 10):
        lieux.update(
            {
                f"lieux-{i}-nom": [""],
                f"lieux-{i}-adresse_lieu_dit": [""],
                f"lieux-{i}-commune": [""],
                f"lieux-{i}-code_insee": [""],
                f"lieux-{i}-departement": [""],
                f"lieux-{i}-site_inspection": [""],
                f"lieux-{i}-wgs84_longitude": [""],
                f"lieux-{i}-wgs84_latitude": [""],
                f"lieux-{i}-activite_etablissement": [""],
                f"lieux-{i}-pays_etablissement": [""],
                f"lieux-{i}-raison_sociale_etablissement": [""],
                f"lieux-{i}-adresse_etablissement": [""],
                f"lieux-{i}-siret_etablissement": [""],
                f"lieux-{i}-code_inupp_etablissement": [""],
                f"lieux-{i}-position_chaine_distribution_etablissement": [""],
            }
        )
    payload = {
        "evenement": ["18585"],
        "action": ["Enregistrer les modifications"],
        "statut_evenement": [""],
        "contexte": [""],
        "date_premier_signalement": [""],
        "commentaire": ["AAAA"],
        "lieux-TOTAL_FORMS": ["10"],
        "lieux-INITIAL_FORMS": ["0"],
        "lieux-MIN_NUM_FORMS": ["0"],
        "lieux-MAX_NUM_FORMS": ["1000"],
        **prelevements,
        **lieux,
        "mesures_conservatoires_immediates": [""],
        "mesures_consignation": [""],
        "mesures_phytosanitaires": [""],
        "mesures_surveillance_specifique": [""],
    }

    fiche_detection = FicheDetectionFactory(evenement__createur=Structure.objects.create(libelle="A new structure"))
    response = client.get(fiche_detection.get_absolute_url())
    assert response.status_code == 403

    response = client.post(reverse("sv:fiche-detection-modification", kwargs={"pk": fiche_detection.pk}), data=payload)

    assert response.status_code == 403
    fiche_detection.refresh_from_db()
    assert fiche_detection.commentaire != "AAAA"


@pytest.mark.django_db
def test_add_lieu_add_and_remove_commune(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    fiche_detection = FicheDetectionFactory()
    lieu = LieuFactory.build(code_insee="17000")

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(fiche_detection)

    lieu_form_elements.open_new_form()
    lieu_form_elements.nom_input.fill(lieu.nom)
    lieu_form_elements.lieu_site_inspection_input.select_option("INCONNU")
    lieu_form_elements.force_commune()
    page.locator("button[aria-label='Remove item: Lille']").click(force=True)
    lieu_form_elements.close_with(action="save")
    evenement_page.save()

    fiche = FicheDetection.objects.get(id=fiche_detection.id)
    lieu_from_db = fiche.lieux.first()
    assert fiche.lieux.count() == 1
    assert lieu_from_db.nom == lieu.nom
    assert lieu_from_db.commune == ""
    assert lieu_from_db.code_insee == ""
    assert lieu_from_db.departement is None


@pytest.mark.django_db
def test_update_prelevement_from_officiel_to_non_officiel_empties_numero_RI(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    prelevement = PrelevementFactory(is_officiel=True, numero_rapport_inspection="12-123456")
    page.goto(f"{live_server.url}{prelevement.lieu.fiche_detection.get_update_url()}")
    page.get_by_test_id("prelevement-update-btn").first.click()
    prelevement_form_elements.prelevement_officiel_checkbox.click()

    expect(prelevement_form_elements.numero_rapport_inspection_input).to_have_value("")
    expect(prelevement_form_elements.numero_rapport_inspection_input).to_be_disabled()


def test_cant_see_update_fiche_detection_btn_if_evenement_is_cloture(live_server, page: Page):
    fiche_detection = FicheDetectionFactory(evenement__etat=Evenement.Etat.CLOTURE)
    page.goto(f"{live_server.url}{fiche_detection.evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Détections")
    expect(page.get_by_role("link", name="Modifier")).not_to_be_visible()


def test_cant_access_update_detection_form_if_evenement_is_cloture(client):
    fiche_detection = FicheDetectionFactory(evenement__etat=Evenement.Etat.CLOTURE)
    response = client.get(fiche_detection.get_update_url())
    assert response.status_code == 403


@pytest.mark.django_db
def test_cant_update_detection_if_evenement_is_cloture(client):
    fiche_detection = FicheDetectionFactory(evenement__etat=Evenement.Etat.CLOTURE)
    response = client.post(fiche_detection.get_update_url(), data={"commentaire": ["AAAA"]})
    assert response.status_code == 403
    fiche_detection.refresh_from_db()
    assert fiche_detection.commentaire != "AAAA"


@pytest.mark.django_db
def test_can_add_commune_to_existing_lieu(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
):
    lieu = LieuFactory(commune="")

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(lieu.fiche_detection)

    lieu_form_elements.edit_form(0)
    lieu_form_elements.force_commune()
    lieu_form_elements.close_with(action="save")
    evenement_page.save()

    lieu.refresh_from_db()
    assert lieu.commune == "Lille"


@pytest.mark.django_db
def test_lieu_for_prelevement_is_correct_when_multiple_lieux(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    """Checks that when editing a Detection the lieu selected for a prelevement is the correct one and
    not the first one of the list"""
    lieu_1 = LieuFactory(nom="Lieu 1")
    lieu_2 = LieuFactory(nom="Lieu 2", fiche_detection=lieu_1.fiche_detection)
    LieuFactory(nom="Lieu 3", fiche_detection=lieu_1.fiche_detection)
    prelevement = PrelevementFactory(lieu=lieu_2, is_officiel=False)

    evenement_page = EvenementUpdatePage(page, live_server)
    evenement_page.navigate(lieu_1.fiche_detection)

    expect(page.locator("#prelevements-list").get_by_text("Lieu 2", exact=True)).to_be_visible()

    page.locator(".prelevement-edit-btn").locator("visible=true").click()
    expect(prelevement_form_elements.lieu_input).to_have_value(lieu_2.nom)
    prelevement_form_elements.numero_echantillon_input.fill("123")
    prelevement_form_elements.save_btn.click()
    evenement_page.save()

    page.get_by_title("Consulter le détail du prélèvement 123").click()
    expect(page.get_by_test_id(f"prelevement-{prelevement.pk}-lieu")).to_have_text("Lieu 2")

    prelevement.refresh_from_db()
    assert prelevement.lieu == lieu_2


def test_elements_infestes_add_new(live_server, page: Page, assert_models_are_equal):
    fiche: FicheDetection = FicheDetectionFactory()

    to_add = ElementInfesteFactory.build_batch(3, espece=EspeceEchantillonFactory())

    evenement_page = EvenementUpdatePage(page, live_server)

    evenement_page.navigate(fiche)
    expect(evenement_page.empty_message).to_be_visible()

    for element in to_add:
        evenement_page.fill_new_form_and_check(element, action="save")

        generated_card = evenement_page.elements_cards.last
        expect(generated_card.locator(".fr-card__title")).to_contain_text(element.get_type_display())
        expect(generated_card.locator(".fr-card__desc")).to_contain_text(f"Espèce végétale : {element.espece}")

        if element.quantite:
            expect(generated_card.locator(".fr-card__desc")).to_contain_text(
                f"Quantité d’éléments infestés : {element.quantite_with_unite}"
            )

    assert fiche.elements_infestes.count() == 0
    expect(evenement_page.empty_message).not_to_be_visible()

    evenement_page.save()

    fiche.refresh_from_db()
    assert fiche.elements_infestes.count() == 3
    for expected, actual in zip(to_add, fiche.elements_infestes.all()):
        assert_models_are_equal(expected, actual, to_exclude=("_state", "id", "fiche_detection_id"))


def test_elements_infestes_add_to_existing(live_server, page: Page, assert_models_are_equal):
    fiche: FicheDetection = FicheDetectionFactory()
    existing = ElementInfesteFactory.create_batch(3, fiche_detection=fiche)

    to_add = ElementInfesteFactory.build_batch(3, espece=EspeceEchantillonFactory())
    to_add_and_delete = ElementInfesteFactory(espece=EspeceEchantillonFactory())

    evenement_page = EvenementUpdatePage(page, live_server)

    evenement_page.navigate(fiche)
    expect(evenement_page.empty_message).not_to_be_visible()

    # First, delete one existing
    evenement_page.remove_last_card()

    for element in (*to_add, to_add_and_delete):
        evenement_page.fill_new_form_and_check(element, action="save")

        generated_card = evenement_page.elements_cards.last
        expect(generated_card.locator(".fr-card__title")).to_contain_text(element.get_type_display())
        expect(generated_card.locator(".fr-card__desc")).to_contain_text(f"Espèce végétale : {element.espece}")

        if element.quantite:
            expect(generated_card.locator(".fr-card__desc")).to_contain_text(
                f"Quantité d’éléments infestés : {element.quantite_with_unite}"
            )
        if element == to_add_and_delete:
            evenement_page.remove_last_card()

    assert fiche.elements_infestes.count() == len(existing)
    expect(evenement_page.empty_message).not_to_be_visible()
    evenement_page.save()

    fiche.refresh_from_db()
    assert fiche.elements_infestes.count() == len(existing[:-1]) + len(to_add)
    for expected, actual in zip((*existing[:-1], *to_add), fiche.elements_infestes.all()):
        assert_models_are_equal(expected, actual, to_exclude=("_state", "id", "fiche_detection_id", "espece_id"))


def test_elements_infestes_remove_all(live_server, page: Page, assert_models_are_equal):
    fiche: FicheDetection = FicheDetectionFactory()
    ElementInfesteFactory.create_batch(3, fiche_detection=fiche)

    evenement_page = EvenementUpdatePage(page, live_server)

    evenement_page.navigate(fiche)
    expect(evenement_page.empty_message).not_to_be_visible()

    while evenement_page.elements_cards.count():
        evenement_page.remove_last_card()

    expect(evenement_page.empty_message).to_be_visible()

    evenement_page.save()

    fiche.refresh_from_db()
    assert fiche.elements_infestes.count() == 0


def test_elements_infestes_edit(live_server, page: Page, assert_models_are_equal):
    fiche: FicheDetection = FicheDetectionFactory()
    elements_infestes = ElementInfesteFactory.create_batch(3, fiche_detection=fiche, quantite="", comments="")

    evenement_page = EvenementUpdatePage(page, live_server)

    fake = Faker()
    idx_to_change = 1
    elements_infeste: ElementInfeste = elements_infestes[idx_to_change]
    new_data = ElementInfesteFactory.create(
        espece=elements_infeste.espece,
        type=fake.random_element([it.value for it in ElementInfesteType if it != elements_infeste.type]),
        quantite="12",
        quantite_unite=ElementInfesteQuantiteUnite.KILOGRAMME,
        comments=fake.paragraph(nb_sentences=5),
    )

    evenement_page.navigate(fiche)
    evenement_page.edit_card(idx_to_change, new_data, close_with_action="save")
    evenement_page.save()

    elements_infeste.refresh_from_db()
    assert_models_are_equal(
        elements_infeste, new_data, fields=("type", "espece", "quantite", "quantite_unite", "comments")
    )


def test_elements_infestes_edit_close_modal_reset_values(live_server, page: Page, choice_js_get_values):
    fiche: FicheDetection = FicheDetectionFactory()
    element_infeste = ElementInfesteFactory(fiche_detection=fiche, espece__libelle="Espece test")
    evenement_page = EvenementUpdatePage(page, live_server)
    new_data = ElementInfesteFactory.create()

    evenement_page.navigate(fiche)
    evenement_page.edit_card(0, new_data, close_with_action="cancel")

    evenement_page.elements_cards.nth(0).get_by_role("button", name="Modifier").click()

    expect(evenement_page.fieldset.get_by_label("Type")).to_have_value(element_infeste.type)
    expect(evenement_page.fieldset.locator('[name$="quantite"]')).to_have_value(element_infeste.quantite)
    expect(
        evenement_page.fieldset.get_by_label(element_infeste.get_quantite_unite_display(), exact=True)
    ).to_be_checked()
    expect(evenement_page.fieldset.locator('[name$="comments"]')).to_have_value(element_infeste.comments)
    assert choice_js_get_values(page, "#id_elements_infestes-0-espece", delete_remove_link=True) == ["Espece test\n"]
