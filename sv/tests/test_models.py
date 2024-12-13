import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from model_bakery import baker
from django.db.utils import IntegrityError

from core.models import Visibilite
from sv.models import (
    FicheZoneDelimitee,
    ZoneInfestee,
    FicheDetection,
    Etat,
    Lieu,
    OrganismeNuisible,
    StatutReglementaire,
    Departement,
    Region,
    Contexte,
    StatutEtablissement,
    PositionChaineDistribution,
    StructurePreleveuse,
    SiteInspection,
    MatricePrelevee,
    EspeceEchantillon,
    LaboratoireAgree,
    LaboratoireConfirmationOfficielle,
    StatutEvenement,
)


@pytest.fixture
def organisme_base():
    return OrganismeNuisible.objects.create(code_oepp="CODE1", libelle_court="Organisme nuisible 1")


@pytest.fixture
def statut_base():
    return StatutReglementaire.objects.create(code="CODE1", libelle="Statut reglementaire 1")


@pytest.fixture
def espece_echantillon_base():
    return EspeceEchantillon.objects.create(code_oepp="CODE1", libelle="Espèce echantillon 1")


@pytest.fixture
def region_base():
    return Region.objects.create(nom="Région 1")


@pytest.fixture
def autre_region():
    return Region.objects.create(nom="Région 2")


@pytest.fixture
def departement_base(region_base):
    return Departement.objects.create(numero="111", nom="Département 111", region=region_base)


@pytest.mark.django_db
def test_fiche_detection_with_no_zones():
    baker.make(FicheDetection, hors_zone_infestee=None, zone_infestee=None)
    assert FicheDetection.objects.count() == 1


@pytest.mark.django_db
def test_fiche_detection_with_zone_infestee():
    baker.make(
        FicheDetection,
        hors_zone_infestee=None,
        zone_infestee=baker.make(ZoneInfestee, fiche_zone_delimitee=baker.make(FicheZoneDelimitee)),
    )
    assert FicheDetection.objects.count() == 1


@pytest.mark.django_db
def test_fiche_detection_with_hors_zone_infestee():
    baker.make(
        FicheDetection,
        hors_zone_infestee=baker.make(FicheZoneDelimitee),
        zone_infestee=None,
    )
    assert FicheDetection.objects.count() == 1


@pytest.mark.django_db
def test_fiche_detection_with_hors_zone_infestee_and_zone_infestee():
    with pytest.raises(IntegrityError):
        baker.make(
            FicheDetection,
            hors_zone_infestee=baker.make(FicheZoneDelimitee),
            zone_infestee=baker.make(ZoneInfestee, fiche_zone_delimitee=baker.make(FicheZoneDelimitee)),
        )


@pytest.mark.django_db
def test_fiche_detection_numero_fiche_is_null_when_visibilite_is_brouillon():
    with pytest.raises(IntegrityError):
        baker.make(
            FicheDetection,
            etat=Etat.objects.get(id=Etat.get_etat_initial()),
            visibilite=Visibilite.BROUILLON,
            _fill_optional=True,
        )


@pytest.mark.django_db
def test_constraint_check_fiche_zone_delimitee_numero_fiche_is_null_when_visibilite_is_brouillon():
    with pytest.raises(IntegrityError):
        baker.make(
            FicheZoneDelimitee,
            etat=Etat.objects.get(id=Etat.get_etat_initial()),
            visibilite=Visibilite.BROUILLON,
            _fill_optional=True,
        )


@pytest.mark.django_db
def test_valid_wgs84_coordinates(fiche_detection):
    lieu = Lieu(
        fiche_detection=fiche_detection, nom="Test", commune="une commune", wgs84_longitude=45.0, wgs84_latitude=45.0
    )
    lieu.full_clean()


@pytest.mark.django_db
def test_invalid_wgs84_longitude(fiche_detection):
    lieu = Lieu(
        fiche_detection=fiche_detection, nom="Test", commune="une commune", wgs84_longitude=181.0, wgs84_latitude=45.0
    )
    with pytest.raises(ValidationError):
        lieu.full_clean()


@pytest.mark.django_db
def test_invalid_wgs84_latitude(fiche_detection):
    lieu = Lieu(
        fiche_detection=fiche_detection, nom="Test", commune="une commune", wgs84_longitude=45.0, wgs84_latitude=91.0
    )
    with pytest.raises(ValidationError):
        lieu.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "test_data,should_raise",
    [
        ({"code_oepp": "CODE1", "libelle_court": "Organisme nuisible 1"}, True),  # Tester le rejet du doublon exact
        (
            {"code_oepp": "CODE1", "libelle_court": "Organisme nuisible 2"},
            True,
        ),  # Tester le rejet du même code avec libellé différent
        (
            {"code_oepp": "CODE2", "libelle_court": "Organisme nuisible 1"},
            True,
        ),  # Tester le rejet du même libellé avec code différent
        (
            {"code_oepp": "CODE2", "libelle_court": "Organisme nuisible 2"},
            False,
        ),  # Tester l'acceptation de valeurs différentes
    ],
)
def test_organisme_nuisible_unique_constraints(test_data, should_raise, organisme_base):
    if should_raise:
        with pytest.raises(IntegrityError):
            OrganismeNuisible.objects.create(**test_data)
    else:
        OrganismeNuisible.objects.create(**test_data)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "test_data,should_raise",
    [
        ({"code": "CODE1", "libelle": "Statut reglementaire 1"}, True),  # Tester le rejet du doublon exact
        (
            {"code": "CODE1", "libelle": "Statut reglementaire 2"},
            True,
        ),  # Tester le rejet du même code avec libellé différent
        (
            {"code": "CODE2", "libelle": "Statut reglementaire 1"},
            True,
        ),  # Tester le rejet du même libellé avec code différent
        ({"code": "CODE2", "libelle": "Statut reglementaire 2"}, False),  # Tester l'acceptation de valeurs différentes
    ],
)
def test_statut_reglementaire_unique_constraints(test_data, should_raise, statut_base):
    if should_raise:
        with pytest.raises(IntegrityError):
            StatutReglementaire.objects.create(**test_data)
    else:
        StatutReglementaire.objects.create(**test_data)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "test_data,should_raise",
    [
        ({"code_oepp": "CODE1", "libelle": "Espèce echantillon 1"}, True),  # Tester le rejet du doublon exact
        (
            {"code_oepp": "CODE1", "libelle": "Espèce echantillon 2"},
            True,
        ),  # Tester le rejet du même code avec libellé différent
        (
            {"code_oepp": "CODE2", "libelle": "Espèce echantillon 1"},
            True,
        ),  # Tester le rejet du même libellé avec code différent
        (
            {"code_oepp": "CODE2", "libelle": "Espèce echantillon 2"},
            False,
        ),  # Tester l'acceptation de valeurs différentes
    ],
)
def test_espece_echantillon_unique_constraints(test_data, should_raise, espece_echantillon_base):
    if should_raise:
        with pytest.raises(IntegrityError):
            EspeceEchantillon.objects.create(**test_data)
    else:
        EspeceEchantillon.objects.create(**test_data)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "test_data,region_fixture,should_raise",
    [
        ({"numero": "111", "nom": "Département 111"}, "region_base", True),  # Tester le rejet du doublon exact
        (
            {"numero": "111", "nom": "Département 222"},
            "region_base",
            True,
        ),  # Tester le rejet du même numéro avec nom différent
        (
            {"numero": "222", "nom": "Département 111"},
            "region_base",
            True,
        ),  # Tester le rejet du même nom avec numéro différent
        (
            {"numero": "222", "nom": "Département 222"},
            "region_base",
            False,
        ),  # Tester l'acceptation de valeurs différentes
        (
            {"numero": "111", "nom": "Département 111"},
            "autre_region",
            True,
        ),  # Tester le rejet même avec région différente
    ],
)
def test_departement_unique_constraints(test_data, region_fixture, should_raise, departement_base, request):
    region = request.getfixturevalue(region_fixture)
    if should_raise:
        with pytest.raises(IntegrityError):
            Departement.objects.create(**test_data, region=region)
    else:
        Departement.objects.create(**test_data, region=region)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_class,field_name,value_prefix",
    [
        (Contexte, "nom", "Contexte"),
        (Region, "nom", "Région"),
        (StatutEtablissement, "libelle", "Statut établissement"),
        (PositionChaineDistribution, "libelle", "Position chaine distribution"),
        (StructurePreleveuse, "nom", "Structure preleveuse"),
        (SiteInspection, "nom", "Site d'inspection"),
        (MatricePrelevee, "libelle", "Matrice prelevee"),
        (LaboratoireAgree, "nom", "Laboratoire agréé"),
        (LaboratoireConfirmationOfficielle, "nom", "Laboratoire de confirmation officielle"),
        (StatutEvenement, "libelle", "Statut de l'événement"),
        (Etat, "libelle", "État"),
    ],
)
def test_unique_constraint(model_class, field_name, value_prefix):
    model_class.objects.create(**{field_name: f"{value_prefix} 1"})

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            model_class.objects.create(**{field_name: f"{value_prefix} 1"})

    model_class.objects.create(**{field_name: f"{value_prefix} 2"})
