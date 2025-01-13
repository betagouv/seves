import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from model_bakery import baker
from reversion.models import Version

from sv.constants import STRUCTURE_EXPLOITANT
from sv.factories import (
    FicheDetectionFactory,
    LieuFactory,
    PrelevementFactory,
    FicheZoneFactory,
    ZoneInfesteeFactory,
    EvenementFactory,
)
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
    StatutEvenement,
    Prelevement,
    Laboratoire,
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


def test_numero_rapport_inspection_format_valide():
    rapport = Prelevement(
        lieu=baker.make(Lieu),
        structure_preleveuse=baker.make(StructurePreleveuse),
        is_officiel=True,
        resultat=Prelevement.Resultat.DETECTE,
        numero_rapport_inspection="24-123456",
    )
    rapport.full_clean()


def test_numero_rapport_inspection_format_invalide():
    rapport = Prelevement(numero_rapport_inspection="24123456")
    with pytest.raises(ValidationError):
        rapport.full_clean()

    rapport = Prelevement(numero_rapport_inspection="2-123456")
    with pytest.raises(ValidationError):
        rapport.full_clean()

    rapport = Prelevement(numero_rapport_inspection="24-12345")
    with pytest.raises(ValidationError):
        rapport.full_clean()


@pytest.mark.django_db
def test_prelevement_not_officiel_cant_have_officiel_related_values():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Prelevement.objects.create(is_officiel=False, numero_rapport_inspection="24-123456")


@pytest.mark.django_db
def test_prelevement_confirmation_cant_have_labo_agree_only():
    labo = Laboratoire.objects.create(nom="Test", confirmation_officielle=False)

    with pytest.raises(ValidationError):
        with transaction.atomic():
            PrelevementFactory(type_analyse=Prelevement.TypeAnalyse.CONFIRMATION, laboratoire=labo)


@pytest.mark.django_db
def test_prelevement_officiel_cant_be_from_exploitant():
    exploitant, _ = StructurePreleveuse.objects.get_or_create(nom=STRUCTURE_EXPLOITANT)

    with pytest.raises(ValidationError):
        Prelevement.objects.create(
            is_officiel=True,
            lieu=baker.make(Lieu),
            resultat=Prelevement.Resultat.DETECTE,
            structure_preleveuse=exploitant,
        )


@pytest.mark.django_db
def test_cant_add_rayon_zone_tampon_negative_in_fiche_zone_delimitee(fiche_zone):
    fiche_zone.rayon_zone_tampon = -1.0
    with pytest.raises(ValidationError) as exc_info:
        fiche_zone.full_clean()
    assert "rayon_zone_tampon" in exc_info.value.error_dict


@pytest.mark.django_db
def test_can_add_rayon_zone_tampon_zero_in_fiche_zone_delimitee(fiche_zone):
    fiche_zone.surface_tampon_totale = None
    fiche_zone.rayon_zone_tampon = 0
    fiche_zone.full_clean()


@pytest.mark.django_db
def test_cant_add_surface_tampon_totale_negative_in_fiche_zone_delimitee(fiche_zone):
    fiche_zone.surface_tampon_totale = -1.0
    with pytest.raises(ValidationError) as exc_info:
        fiche_zone.full_clean()
    assert "surface_tampon_totale" in exc_info.value.error_dict


@pytest.mark.django_db
def test_can_add_surface_tampon_totale_zero_in_fiche_zone_delimitee(fiche_zone):
    fiche_zone.rayon_zone_tampon = None
    fiche_zone.surface_tampon_totale = 0
    fiche_zone.full_clean()


@pytest.mark.django_db
def test_cant_add_rayon_negative_in_zone_infestee(fiche_zone):
    zone = ZoneInfestee(rayon=-1.0, fiche_zone_delimitee=fiche_zone)
    with pytest.raises(ValidationError) as exc_info:
        zone.full_clean()
    assert "rayon" in exc_info.value.error_dict


@pytest.mark.django_db
def test_can_add_rayon_zero_in_zone_infestee(fiche_zone):
    zone = ZoneInfestee(rayon=0, fiche_zone_delimitee=fiche_zone)
    zone.full_clean()


@pytest.mark.django_db
def test_cant_add_surface_infestee_totale_negative_in_zone_infestee(fiche_zone):
    zone = ZoneInfestee(surface_infestee_totale=-1.0, fiche_zone_delimitee=fiche_zone)
    with pytest.raises(ValidationError) as exc_info:
        zone.full_clean()
    assert "surface_infestee_totale" in exc_info.value.error_dict


@pytest.mark.django_db
def test_can_add_surface_infestee_totale_zero_in_zone_infestee(fiche_zone):
    zone = ZoneInfestee(surface_infestee_totale=0, fiche_zone_delimitee=fiche_zone)
    zone.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "test_data,should_raise",
    [
        # Tester le rejet du doublon exact
        ({"code_oepp": "CODE1", "libelle_court": "Organisme nuisible 1"}, True),
        # Tester le rejet du même code avec libellé différent
        (
            {"code_oepp": "CODE1", "libelle_court": "Organisme nuisible 2"},
            True,
        ),
        # Tester le rejet du même libellé avec code différent
        (
            {"code_oepp": "CODE2", "libelle_court": "Organisme nuisible 1"},
            True,
        ),
        # Tester l'acceptation de valeurs différentes
        (
            {"code_oepp": "CODE2", "libelle_court": "Organisme nuisible 2"},
            False,
        ),
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
        # Tester le rejet du doublon exact
        ({"code": "CODE1", "libelle": "Statut reglementaire 1"}, True),
        # Tester le rejet du même code avec libellé différent
        (
            {"code": "CODE1", "libelle": "Statut reglementaire 2"},
            True,
        ),
        # Tester le rejet du même libellé avec code différent
        (
            {"code": "CODE2", "libelle": "Statut reglementaire 1"},
            True,
        ),
        # Tester l'acceptation de valeurs différentes
        ({"code": "CODE2", "libelle": "Statut reglementaire 2"}, False),
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
        # Tester le rejet du doublon exact
        ({"code_oepp": "CODE1", "libelle": "Espèce echantillon 1"}, True),
        # Tester le rejet du même code avec libellé différent
        (
            {"code_oepp": "CODE1", "libelle": "Espèce echantillon 2"},
            True,
        ),
        # Tester le rejet du même libellé avec code différent
        (
            {"code_oepp": "CODE2", "libelle": "Espèce echantillon 1"},
            True,
        ),
        # Tester l'acceptation de valeurs différentes
        (
            {"code_oepp": "CODE2", "libelle": "Espèce echantillon 2"},
            False,
        ),
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
        # Tester le rejet du doublon exact
        ({"numero": "111", "nom": "Département 111"}, "region_base", True),
        # Tester le rejet du même numéro avec nom différent
        (
            {"numero": "111", "nom": "Département 222"},
            "region_base",
            True,
        ),
        # Tester le rejet du même nom avec numéro différent
        (
            {"numero": "222", "nom": "Département 111"},
            "region_base",
            True,
        ),
        # Tester l'acceptation de valeurs différentes
        (
            {"numero": "222", "nom": "Département 222"},
            "region_base",
            False,
        ),
        # Tester le rejet même avec région différente
        (
            {"numero": "111", "nom": "Département 111"},
            "autre_region",
            True,
        ),
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
        (Laboratoire, "nom", "Laboratoire"),
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


@pytest.mark.django_db
def test_fiche_detection_latest_revision():
    fiche_detection = FicheDetectionFactory()
    assert fiche_detection.latest_version is not None
    latest_version = fiche_detection.latest_version

    fiche_detection.commentaire = "Lorem"
    fiche_detection.save()
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created

    latest_version = fiche_detection.latest_version
    lieu = LieuFactory(fiche_detection=fiche_detection, nom="Maison")
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created
    assert fiche_detection.latest_version.revision.comment == "Le lieu 'Maison' a été ajouté à la fiche"

    latest_version = fiche_detection.latest_version
    lieu.nom = "Nouvelle maison"
    lieu.save()
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created

    latest_version = fiche_detection.latest_version
    structure_sivep, _ = StructurePreleveuse.objects.get_or_create(nom="SIVEP")
    prelevement = PrelevementFactory(lieu=lieu, structure_preleveuse=structure_sivep)
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created
    assert (
        fiche_detection.latest_version.revision.comment
        == "Le prélèvement pour le lieu 'Nouvelle maison' et la structure 'SIVEP' a été ajouté à la fiche"
    )

    latest_version = fiche_detection.latest_version
    new_structure, _ = StructurePreleveuse.objects.get_or_create(nom="SEMAE")
    prelevement.structure_preleveuse = new_structure
    prelevement.save()
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created

    latest_version = fiche_detection.latest_version
    prelevement.delete()
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created
    assert (
        fiche_detection.latest_version.revision.comment
        == "Le prélèvement pour le lieu 'Nouvelle maison' et la structure 'SEMAE' a été supprimé de la fiche"
    )

    latest_version = fiche_detection.latest_version
    lieu.delete()
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created
    assert fiche_detection.latest_version.revision.comment == "Le lieu 'Nouvelle maison' a été supprimé de la fiche"


@pytest.mark.django_db
def test_fiche_detection_latest_revision_performances(django_assert_num_queries):
    prelevement = PrelevementFactory()
    fiche_detection = prelevement.lieu.fiche_detection
    lieu_2 = LieuFactory(fiche_detection=fiche_detection)
    lieu_1 = LieuFactory(fiche_detection=fiche_detection)
    PrelevementFactory(lieu=lieu_1)
    PrelevementFactory(lieu=lieu_2)
    PrelevementFactory(lieu=lieu_2)

    with django_assert_num_queries(5):
        assert fiche_detection.latest_version is not None

    LieuFactory(fiche_detection=fiche_detection)
    PrelevementFactory(lieu__fiche_detection=fiche_detection)

    with django_assert_num_queries(5):
        assert fiche_detection.latest_version is not None


@pytest.mark.django_db
def test_fiche_zone_delimitee_latest_revision():
    fiche_zone_delimitee = FicheZoneFactory()
    assert fiche_zone_delimitee.latest_version is not None
    latest_version = fiche_zone_delimitee.latest_version

    fiche_zone_delimitee.commentaire = "Lorem"
    fiche_zone_delimitee.save()
    assert latest_version.pk != fiche_zone_delimitee.latest_version.pk
    assert latest_version.revision.date_created < fiche_zone_delimitee.latest_version.revision.date_created

    latest_version = fiche_zone_delimitee.latest_version
    zone_infestee = ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone_delimitee, nom="Zone 3")
    assert latest_version.pk != fiche_zone_delimitee.latest_version.pk
    assert latest_version.revision.date_created < fiche_zone_delimitee.latest_version.revision.date_created
    assert fiche_zone_delimitee.latest_version.revision.comment == "La zone infestée 'Zone 3' a été ajoutée à la fiche"

    latest_version = fiche_zone_delimitee.latest_version
    zone_infestee.nom = "Zone 4"
    zone_infestee.save()
    assert latest_version.pk != fiche_zone_delimitee.latest_version.pk
    assert latest_version.revision.date_created < fiche_zone_delimitee.latest_version.revision.date_created

    latest_version = fiche_zone_delimitee.latest_version
    zone_infestee.delete()
    assert latest_version.pk != fiche_zone_delimitee.latest_version.pk
    assert latest_version.revision.date_created < fiche_zone_delimitee.latest_version.revision.date_created
    assert (
        fiche_zone_delimitee.latest_version.revision.comment == "La zone infestée 'Zone 4' a été supprimée de la fiche"
    )


@pytest.mark.django_db
def test_evenement_latest_revision():
    evenement = EvenementFactory()
    assert evenement.latest_version is not None
    latest_version = evenement.latest_version

    evenement.is_deleted = True
    evenement.save()
    assert latest_version.pk != evenement.latest_version.pk
    assert latest_version.revision.date_created < evenement.latest_version.revision.date_created


@pytest.mark.django_db
def test_evenement_latest_revision_performances(django_assert_num_queries):
    evenement = EvenementFactory()

    with django_assert_num_queries(2):
        assert evenement.latest_version is not None

    fiche_detection = FicheDetectionFactory(evenement=evenement)
    with django_assert_num_queries(5):
        assert evenement.latest_version is not None

    lieu_2 = LieuFactory(fiche_detection=fiche_detection)
    lieu_1 = LieuFactory(fiche_detection=fiche_detection)
    PrelevementFactory(lieu=lieu_1)
    PrelevementFactory(lieu=lieu_2)
    PrelevementFactory(lieu=lieu_2)

    with django_assert_num_queries(7):
        assert evenement.latest_version is not None


@pytest.mark.django_db
def test_change_zone_infestee_creates_revision_on_zone_infestee():
    fiche_detection = FicheDetectionFactory(zone_infestee=None)
    zone_infestee = ZoneInfesteeFactory()
    latest_version = fiche_detection.latest_version

    fiche_detection.zone_infestee = zone_infestee
    fiche_detection.save()

    assert latest_version.pk == fiche_detection.latest_version.pk
    version = Version.objects.get_for_object(zone_infestee).first()
    assert version.revision.comment == f"La fiche détection '{fiche_detection.pk}' a été ajoutée en zone infestée"

    fiche_detection.zone_infestee = None
    fiche_detection.save()

    assert latest_version.pk == fiche_detection.latest_version.pk
    version = Version.objects.get_for_object(zone_infestee).first()
    assert version.revision.comment == f"La fiche détection '{fiche_detection.pk}' a été retirée de la zone infestée"


@pytest.mark.django_db
def test_change_hors_zone_infestee_creates_revision_on_zone_infestee():
    fiche_detection = FicheDetectionFactory(zone_infestee=None)
    fiche_zone_delimitee = FicheZoneFactory()
    latest_version = fiche_detection.latest_version

    fiche_detection.hors_zone_infestee = fiche_zone_delimitee
    fiche_detection.save()

    assert latest_version.pk == fiche_detection.latest_version.pk
    version = Version.objects.get_for_object(fiche_zone_delimitee).first()
    assert version.revision.comment == f"La fiche détection '{fiche_detection.pk}' a été ajoutée en hors zone infestée"

    fiche_detection.hors_zone_infestee = None
    fiche_detection.save()

    assert latest_version.pk == fiche_detection.latest_version.pk
    version = Version.objects.get_for_object(fiche_zone_delimitee).first()
    assert version.revision.comment == f"La fiche détection '{fiche_detection.pk}' a été retirée en hors zone infestée"
