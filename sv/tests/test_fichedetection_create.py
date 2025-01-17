from datetime import datetime

import pytest
from django.conf import settings
from django.urls import reverse
from model_bakery import baker
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE
from core.models import Contact, Visibilite
from sv.constants import REGIONS, DEPARTEMENTS
from sv.constants import STATUTS_EVENEMENT, STATUTS_REGLEMENTAIRES, CONTEXTES
from .conftest import check_select_options
from .test_utils import FicheDetectionFormDomElements, LieuFormDomElements, PrelevementFormDomElements
from ..models import (
    FicheDetection,
    StatutEvenement,
    StatutReglementaire,
    Contexte,
    OrganismeNuisible,
    Lieu,
    Departement,
    PositionChaineDistribution,
    Region,
    StructurePreleveuse,
    SiteInspection,
)


@pytest.fixture(autouse=True)
def create_fixtures_if_needed(db):
    for statut in STATUTS_EVENEMENT:
        StatutEvenement.objects.get_or_create(libelle=statut)

    OrganismeNuisible.objects.get_or_create(
        libelle_court="Xylella fastidiosa (maladie de Pierce)", defaults={"code_oepp": "OE_XYLEFA"}
    )
    OrganismeNuisible.objects.get_or_create(libelle_court="lorem ipsum", defaults={"code_oepp": "LOREM"})

    for code, libelle in STATUTS_REGLEMENTAIRES.items():
        StatutReglementaire.objects.get_or_create(code=code, libelle=libelle)

    for contexte in CONTEXTES:
        Contexte.objects.get_or_create(nom=contexte)

    for nom in REGIONS:
        Region.objects.get_or_create(nom=nom)
    for numero, nom, region_nom in DEPARTEMENTS:
        region = Region.objects.get(nom=region_nom)
        Departement.objects.get_or_create(numero=numero, nom=nom, region=region)


def test_page_title(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    expect(page.get_by_role("heading", name="Création d'une fiche détection", exact=True)).to_be_visible()


def test_new_fiche_detection_form_content(live_server, page: Page, form_elements: FicheDetectionFormDomElements):
    """Test que la page de création de fiche de détection contient bien les labels et les champs attendus."""
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    expect(form_elements.informations_title).to_be_visible()
    expect(form_elements.objet_evenement_title).to_be_visible()
    expect(form_elements.lieux_title).to_be_visible()
    expect(form_elements.prelevements_title).to_be_visible()
    expect(form_elements.mesures_gestion_title).to_be_visible()
    expect(form_elements.publish_btn).to_be_visible()
    expect(form_elements.add_lieu_btn).to_be_visible()
    expect(form_elements.add_prelevement_btn).to_be_disabled()

    expect(form_elements.date_creation_label).to_be_visible()
    expect(form_elements.date_creation_input).to_be_disabled()

    expect(form_elements.statut_evenement_label).to_be_visible()
    expect(form_elements.statut_evenement_input).to_be_visible()
    expect(form_elements.numero_europhyt_label).not_to_be_visible()
    expect(form_elements.numero_europhyt_input).not_to_be_visible()
    expect(form_elements.numero_rasff_label).not_to_be_visible()
    expect(form_elements.numero_rasff_input).not_to_be_visible()
    expect(form_elements.statut_evenement_input).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(form_elements.statut_evenement_input).to_have_value("")
    statuts_evenement = list(StatutEvenement.objects.values_list("libelle", flat=True))
    check_select_options(page, "Statut évènement", statuts_evenement)

    expect(form_elements.organisme_nuisible_label).to_be_visible()
    expect(form_elements.organisme_nuisible_input).to_contain_text(settings.SELECT_EMPTY_CHOICE)

    expect(form_elements.statut_reglementaire_label).to_be_visible()
    expect(form_elements.statut_reglementaire_input).to_be_visible()
    expect(form_elements.statut_reglementaire_input).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(form_elements.statut_reglementaire_input).to_have_value("")
    statuts_reglementaire = list(StatutReglementaire.objects.values_list("libelle", flat=True))
    check_select_options(page, "Statut réglementaire", statuts_reglementaire)

    expect(form_elements.contexte_label).to_be_visible()
    expect(form_elements.contexte_input).to_be_visible()
    expect(form_elements.contexte_input).to_contain_text(settings.SELECT_EMPTY_CHOICE)
    expect(form_elements.contexte_input).to_have_value("")
    contextes = list(Contexte.objects.values_list("nom", flat=True))
    check_select_options(page, "Contexte", contextes)

    expect(form_elements.date_1er_signalement_label).to_be_visible()
    expect(form_elements.date_1er_signalement_input).to_be_visible()
    expect(form_elements.date_1er_signalement_input).to_be_empty()

    expect(form_elements.commentaire_label).to_be_visible()
    expect(form_elements.commentaire_input).to_be_visible()
    expect(form_elements.commentaire_input).to_be_empty()

    expect(form_elements.vegetaux_infestes_label).to_be_visible()
    expect(form_elements.vegetaux_infestes_input).to_be_visible()
    expect(form_elements.vegetaux_infestes_input).to_be_empty()

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
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, mocked_authentification_user, choice_js_fill
):
    statut_evenement = StatutEvenement.objects.first()
    organisme_nuisible = OrganismeNuisible.objects.get(libelle_court="Xylella fastidiosa (maladie de Pierce)")
    statut_reglementaire = StatutReglementaire.objects.first()
    contexte = Contexte.objects.first()

    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    """Test que les informations de la fiche de détection sont bien enregistrées après création."""
    page.get_by_label("Statut évènement").select_option(value=str(statut_evenement.id))
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "xylela", organisme_nuisible.libelle_court)
    page.get_by_label("Statut réglementaire").select_option(value=str(statut_reglementaire.id))
    page.get_by_label("Contexte").select_option(value=str(contexte.id))
    page.get_by_label("Date 1er signalement").fill("2024-04-21")
    page.get_by_label("Commentaire").fill("test commentaire")
    page.get_by_label("Végétaux infestés").fill("3 citronniers")
    page.get_by_label("Mesures conservatoires immédiates").fill("test mesures conservatoires")
    page.get_by_label("Mesures de consignation").fill("test mesures consignation")
    page.get_by_label("Mesures phytosanitaires").fill("test mesures phyto")
    page.get_by_label("Mesures de surveillance spécifique").fill("test mesures surveillance")
    page.get_by_role("button", name="Enregistrer").click()

    page.wait_for_timeout(600)

    fiche_detection = FicheDetection.objects.get()
    assert fiche_detection.createur == mocked_authentification_user.agent.structure
    assert fiche_detection.statut_evenement.libelle == statut_evenement.libelle
    assert fiche_detection.evenement.organisme_nuisible.libelle_court == organisme_nuisible.libelle_court
    assert fiche_detection.evenement.statut_reglementaire.id == statut_reglementaire.id
    assert fiche_detection.contexte.id == contexte.id
    assert fiche_detection.date_premier_signalement.strftime("%Y-%m-%d") == "2024-04-21"
    assert fiche_detection.commentaire == "test commentaire"
    assert fiche_detection.vegetaux_infestes == "3 citronniers"
    assert fiche_detection.mesures_conservatoires_immediates == "test mesures conservatoires"
    assert fiche_detection.mesures_consignation == "test mesures consignation"
    assert fiche_detection.mesures_phytosanitaires == "test mesures phyto"
    assert fiche_detection.mesures_surveillance_specifique == "test mesures surveillance"


@pytest.mark.django_db
def test_fiche_detection_create_as_ac_can_access_rasff_europhyt(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, choice_js_fill, mocked_authentification_user
):
    structure = mocked_authentification_user.agent.structure
    structure.niveau1 = AC_STRUCTURE
    structure.save()
    organisme_nuisible, _ = OrganismeNuisible.objects.get_or_create(
        libelle_court="Mon ON",
    )

    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "Mon ON", "Mon ON")
    form_elements.statut_reglementaire_input.select_option("organisme quarantaine")
    page.get_by_label("Numéro Europhyt").fill("1" * 8)
    page.get_by_label("Numéro Rasff").fill("2" * 9)
    page.get_by_role("button", name="Enregistrer").click()
    page.wait_for_timeout(600)

    fiche_detection = FicheDetection.objects.get()
    assert fiche_detection.numero_europhyt == "11111111"
    assert fiche_detection.numero_rasff == "222222222"


@pytest.mark.django_db
def test_create_fiche_detection_with_lieu(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
    mocked_authentification_user,
    fill_commune,
    choice_js_fill,
):
    organisme_nuisible, _ = OrganismeNuisible.objects.get_or_create(
        libelle_court="Mon ON",
    )
    dept = baker.make(Departement)
    site_inspection = baker.make(SiteInspection)
    position = baker.make(PositionChaineDistribution)
    lieu = baker.prepare(
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
    )

    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    expect(form_elements.add_prelevement_btn).to_be_disabled()
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "Mon ON", "Mon ON")
    form_elements.statut_reglementaire_input.select_option("organisme quarantaine")
    form_elements.add_lieu_btn.click()
    page.wait_for_timeout(200)
    lieu_form_elements.nom_input.fill(lieu.nom)
    lieu_form_elements.adresse_input.fill(lieu.adresse_lieu_dit)
    fill_commune(page)
    lieu_form_elements.coord_gps_wgs84_latitude_input.fill(str(lieu.wgs84_latitude))
    lieu_form_elements.coord_gps_wgs84_longitude_input.fill(str(lieu.wgs84_longitude))
    lieu_form_elements.is_etablissement_checkbox.click(force=True)
    lieu_form_elements.nom_etablissement_input.fill(lieu.nom_etablissement)
    lieu_form_elements.activite_etablissement_input.fill(lieu.activite_etablissement)
    lieu_form_elements.pays_etablissement_input.fill(lieu.pays_etablissement)
    lieu_form_elements.raison_sociale_etablissement_input.fill(lieu.raison_sociale_etablissement)
    lieu_form_elements.adresse_etablissement_input.fill(lieu.adresse_etablissement)
    lieu_form_elements.siret_etablissement_input.fill(lieu.siret_etablissement)
    lieu_form_elements.code_inupp_etablissement_input.fill(lieu.code_inupp_etablissement)
    lieu_form_elements.lieu_site_inspection_input.select_option(str(lieu.site_inspection.id))
    lieu_form_elements.position_etablissement_input.select_option(
        str(lieu.position_chaine_distribution_etablissement.id)
    )
    lieu_form_elements.save_btn.click()
    expect(form_elements.add_prelevement_btn).to_be_enabled()
    form_elements.publish_btn.click()

    page.wait_for_timeout(1000)

    fiche_detection = FicheDetection.objects.get()
    lieu_from_db = fiche_detection.lieux.get()
    assert lieu_from_db.nom == lieu.nom
    assert lieu_from_db.wgs84_latitude == lieu.wgs84_latitude
    assert lieu_from_db.wgs84_longitude == lieu.wgs84_longitude
    assert lieu_from_db.adresse_lieu_dit == lieu.adresse_lieu_dit
    assert lieu_from_db.commune == "Lille"
    assert lieu_from_db.code_insee == "59350"
    assert lieu_from_db.departement == Departement.objects.get(nom="Nord")
    assert lieu_from_db.is_etablissement == lieu.is_etablissement
    assert lieu_from_db.nom_etablissement == lieu.nom_etablissement
    assert lieu_from_db.activite_etablissement == lieu.activite_etablissement
    assert lieu_from_db.pays_etablissement == lieu.pays_etablissement
    assert lieu_from_db.raison_sociale_etablissement == lieu.raison_sociale_etablissement
    assert lieu_from_db.adresse_etablissement == lieu.adresse_etablissement
    assert lieu_from_db.siret_etablissement == lieu.siret_etablissement
    assert lieu_from_db.code_inupp_etablissement == lieu.code_inupp_etablissement
    assert lieu_from_db.site_inspection == lieu.site_inspection
    assert lieu_from_db.position_chaine_distribution_etablissement == lieu.position_chaine_distribution_etablissement


def test_structure_contact_is_add_to_contacts_list_when_fiche_detection_is_created(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, mocked_authentification_user, choice_js_fill
):
    """Test que lors de la création d'une fiche de détection, le contact correspondant à la structure de l'utilisateur connecté
    est ajouté dans la liste des contacts de l'événement"""
    organisme_nuisible, _ = OrganismeNuisible.objects.get_or_create(
        libelle_court="Mon ON",
    )
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "Mon ON", "Mon ON")
    form_elements.statut_reglementaire_input.select_option("organisme quarantaine")
    form_elements.publish_btn.click()

    fiche_detection = FicheDetection.objects.get()
    fiche_detection.evenement.visibilite = Visibilite.LOCALE
    fiche_detection.evenement.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    page.get_by_test_id("contacts").click()
    expect(page.get_by_text(str(mocked_authentification_user.agent), exact=True)).to_be_visible()

    page.wait_for_timeout(600)

    fiche_detection = FicheDetection.objects.last()
    user_contact_structure = Contact.objects.get(structure=mocked_authentification_user.agent.structure)
    assert user_contact_structure in fiche_detection.evenement.contacts.all()


def test_agent_contact_is_add_to_contacts_list_when_fiche_detection_is_created(
    live_server, page: Page, choice_js_fill, form_elements: FicheDetectionFormDomElements, mocked_authentification_user
):
    """Test que lors de la création d'une fiche de détection, le contact correspondant à l'agent de l'utilisateur connecté
    est ajouté dans la liste des contacts de l'événement"""
    organisme_nuisible, _ = OrganismeNuisible.objects.get_or_create(
        libelle_court="Mon ON",
    )
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "Mon ON", "Mon ON")
    form_elements.statut_reglementaire_input.select_option("organisme quarantaine")
    form_elements.publish_btn.click()

    page.wait_for_timeout(600)

    fiche_detection = FicheDetection.objects.last()
    user_contact_agent = Contact.objects.get(agent=mocked_authentification_user.agent)
    assert user_contact_agent in fiche_detection.evenement.contacts.all()


def test_add_lieu_with_name_only_and_save(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    choice_js_fill,
    lieu_form_elements: LieuFormDomElements,
):
    organisme_nuisible, _ = OrganismeNuisible.objects.get_or_create(
        libelle_court="Mon ON",
    )
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "Mon ON", "Mon ON")
    form_elements.statut_reglementaire_input.select_option("organisme quarantaine")
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.click()
    lieu_form_elements.nom_input.fill("Chez moi")
    lieu_form_elements.save_btn.click()
    form_elements.publish_btn.click()

    page.wait_for_timeout(600)

    fiche = FicheDetection.objects.get()
    lieu = fiche.lieux.get()
    assert lieu.nom == "Chez moi"


@pytest.mark.django_db
def test_fiche_detection_status_reglementaire_is_pre_selected(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, choice_js_fill
):
    statut = StatutReglementaire.objects.get(code="OQ")
    organisme_nuisible, _ = OrganismeNuisible.objects.get_or_create(code_oepp="XYLEFM")
    organisme_nuisible.libelle_court = "Mon ON"
    organisme_nuisible.save()

    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "Mon ON", "Mon ON")
    expect(form_elements.statut_reglementaire_input).to_have_value(str(statut.id))
    page.get_by_role("button", name="Enregistrer").click()

    page.wait_for_timeout(600)

    fiche_detection = FicheDetection.objects.get()
    assert fiche_detection.evenement.organisme_nuisible == organisme_nuisible
    assert fiche_detection.evenement.statut_reglementaire.code == "OQ"


@pytest.mark.django_db
def test_fiche_detection_status_reglementaire_is_emptied_when_unknown(
    live_server, page: Page, form_elements: FicheDetectionFormDomElements, choice_js_fill
):
    statut = StatutReglementaire.objects.get(code="OQ")
    organisme_nuisible, _ = OrganismeNuisible.objects.get_or_create(code_oepp="XYLEFM")
    organisme_nuisible.libelle_court = "Mon ON"
    organisme_nuisible.save()

    organisme_nuisible_no_status, _ = OrganismeNuisible.objects.get_or_create(code_oepp="FOO")
    organisme_nuisible_no_status.libelle_court = "Pas mon ON"
    organisme_nuisible_no_status.save()

    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "Mon ON", "Mon ON")
    expect(form_elements.statut_reglementaire_input).to_have_value(str(statut.id))
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "Pas mon ON", "Pas mon ON")
    expect(form_elements.statut_reglementaire_input).to_have_value("")


def test_prelevements_are_always_linked_to_lieu(
    live_server,
    page: Page,
    form_elements: FicheDetectionFormDomElements,
    lieu_form_elements: LieuFormDomElements,
    prelevement_form_elements: PrelevementFormDomElements,
    choice_js_fill,
):
    organisme_nuisible, _ = OrganismeNuisible.objects.get_or_create(
        libelle_court="Mon ON",
    )
    structures = baker.make(StructurePreleveuse, _quantity=2)
    page.wait_for_timeout(600)
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "Mon ON", "Mon ON")
    form_elements.statut_reglementaire_input.select_option("organisme quarantaine")
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.fill("un lieu")
    lieu_form_elements.save_btn.click()
    for _ in range(2):
        form_elements.add_prelevement_btn.click()
        prelevement_form_elements.structure_input.select_option(str(structures[0].id))
        prelevement_form_elements.resultat_input("detecte").click()
        prelevement_form_elements.type_analyse_input("première intention").click()
        prelevement_form_elements.save_btn.click()
    form_elements.publish_btn.click()
    page.wait_for_timeout(600)

    lieu = FicheDetection.objects.get().lieux.get()
    prelevements = lieu.prelevements.all()
    for prelevement in prelevements:
        assert prelevement.lieu == lieu


@pytest.mark.django_db
def test_one_fiche_detection_is_created_when_double_click_on_save_btn(
    live_server, form_elements, choice_js_fill, page: Page
):
    organisme_nuisible, _ = OrganismeNuisible.objects.get_or_create(
        libelle_court="Mon ON",
    )
    page.goto(f"{live_server.url}{reverse('fiche-detection-creation')}")
    choice_js_fill(page, "#organisme-nuisible .choices__list--single", "Mon ON", "Mon ON")
    form_elements.statut_reglementaire_input.select_option("organisme quarantaine")
    page.get_by_role("button", name="Enregistrer").dblclick()
    page.wait_for_timeout(600)
    assert FicheDetection.objects.count() == 1
