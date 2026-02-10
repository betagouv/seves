from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
import pytest
from reversion.models import Version

from core.factories import DocumentFactory, StructureFactory
from core.models import Document, Visibilite
from sv.constants import STRUCTURE_EXPLOITANT
from sv.factories import (
    EvenementFactory,
    FicheDetectionFactory,
    FicheZoneFactory,
    LieuFactory,
    PrelevementFactory,
    StructurePreleveuseFactory,
    ZoneInfesteeFactory,
)
from sv.models import (
    Contexte,
    Departement,
    EspeceEchantillon,
    FicheDetection,
    Laboratoire,
    Lieu,
    MatricePrelevee,
    OrganismeNuisible,
    PositionChaineDistribution,
    Prelevement,
    Region,
    SiteInspection,
    StatutEtablissement,
    StatutEvenement,
    StatutReglementaire,
    StructurePreleveuse,
    VersionFicheZoneDelimitee,
    ZoneInfestee,
)


@pytest.fixture
def organisme_base():
    return OrganismeNuisible.objects.create(
        code_oepp="CODE1", libelle_court="Organisme nuisible 1", libelle_long="Organisme nuisible 1"
    )


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
    FicheDetectionFactory(hors_zone_infestee=None, zone_infestee=None)
    assert FicheDetection.objects.count() == 1


@pytest.mark.django_db
def test_fiche_detection_with_zone_infestee():
    FicheDetectionFactory(hors_zone_infestee=None, zone_infestee=ZoneInfesteeFactory())
    assert FicheDetection.objects.count() == 1


@pytest.mark.django_db
def test_fiche_detection_with_hors_zone_infestee():
    FicheDetectionFactory(hors_zone_infestee=FicheZoneFactory(), zone_infestee=None)
    assert FicheDetection.objects.count() == 1


@pytest.mark.django_db
def test_fiche_detection_with_hors_zone_infestee_and_zone_infestee():
    with pytest.raises(IntegrityError):
        FicheDetectionFactory(hors_zone_infestee=FicheZoneFactory(), zone_infestee=ZoneInfesteeFactory())


@pytest.mark.django_db
def test_valid_wgs84_coordinates():
    fiche_detection = FicheDetectionFactory()
    lieu = Lieu(
        fiche_detection=fiche_detection, nom="Test", commune="une commune", wgs84_longitude=45.0, wgs84_latitude=45.0
    )
    lieu.full_clean()


@pytest.mark.django_db
def test_invalid_wgs84_longitude():
    fiche_detection = FicheDetectionFactory()
    lieu = Lieu(
        fiche_detection=fiche_detection, nom="Test", commune="une commune", wgs84_longitude=181.0, wgs84_latitude=45.0
    )
    with pytest.raises(ValidationError):
        lieu.full_clean()


@pytest.mark.django_db
def test_invalid_wgs84_latitude():
    fiche_detection = FicheDetectionFactory()
    lieu = Lieu(
        fiche_detection=fiche_detection, nom="Test", commune="une commune", wgs84_longitude=45.0, wgs84_latitude=91.0
    )
    with pytest.raises(ValidationError):
        lieu.full_clean()


def test_numero_rapport_inspection_format_valide():
    rapport = Prelevement(
        lieu=LieuFactory(),
        structure_preleveuse=StructurePreleveuseFactory(not_exploitant=True),
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
            lieu=LieuFactory(),
            resultat=Prelevement.Resultat.DETECTE,
            structure_preleveuse=exploitant,
        )


@pytest.mark.django_db
def test_cant_add_rayon_zone_tampon_negative_in_fiche_zone_delimitee():
    fiche_zone = FicheZoneFactory(rayon_zone_tampon=-1.0)
    with pytest.raises(ValidationError) as exc_info:
        fiche_zone.full_clean()
    assert "rayon_zone_tampon" in exc_info.value.error_dict


@pytest.mark.django_db
def test_can_add_rayon_zone_tampon_zero_in_fiche_zone_delimitee():
    FicheZoneFactory(surface_tampon_totale=None, rayon_zone_tampon=0)


@pytest.mark.django_db
def test_cant_add_surface_tampon_totale_negative_in_fiche_zone_delimitee():
    fiche_zone = FicheZoneFactory(surface_tampon_totale=-1.0)
    with pytest.raises(ValidationError) as exc_info:
        fiche_zone.full_clean()
    assert "surface_tampon_totale" in exc_info.value.error_dict


@pytest.mark.django_db
def test_can_add_surface_tampon_totale_zero_in_fiche_zone_delimitee():
    FicheZoneFactory(rayon_zone_tampon=None, surface_tampon_totale=0)


@pytest.mark.django_db
def test_cant_add_rayon_negative_in_zone_infestee():
    zone = ZoneInfestee(rayon=-1.0, fiche_zone_delimitee=FicheZoneFactory())
    with pytest.raises(ValidationError) as exc_info:
        zone.full_clean()
    assert "rayon" in exc_info.value.error_dict


@pytest.mark.django_db
def test_can_add_rayon_zero_in_zone_infestee():
    zone = ZoneInfestee(rayon=0, fiche_zone_delimitee=FicheZoneFactory())
    zone.full_clean()


@pytest.mark.django_db
def test_cant_add_surface_infestee_totale_negative_in_zone_infestee():
    zone = ZoneInfestee(surface_infestee_totale=-1.0, fiche_zone_delimitee=FicheZoneFactory())
    with pytest.raises(ValidationError) as exc_info:
        zone.full_clean()
    assert "surface_infestee_totale" in exc_info.value.error_dict


@pytest.mark.django_db
def test_can_add_surface_infestee_totale_zero_in_zone_infestee():
    zone = ZoneInfestee(surface_infestee_totale=0, fiche_zone_delimitee=FicheZoneFactory())
    zone.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "test_data,should_raise",
    [
        # Tester le rejet du doublon exact
        ({"code_oepp": "CODE1", "libelle_court": "Organisme nuisible 1", "libelle_long": "Organisme nuisible 1"}, True),
        # Tester le rejet du même code avec libellé différent
        (
            {"code_oepp": "CODE1", "libelle_court": "Organisme nuisible 2", "libelle_long": "Organisme nuisible 2"},
            True,
        ),
        # Tester le rejet du même libellé avec code différent
        (
            {"code_oepp": "CODE2", "libelle_court": "Organisme nuisible 1", "libelle_long": "Organisme nuisible 1"},
            True,
        ),
        # Tester le rejet du même libellé long avec code différent
        (
            {"code_oepp": "CODE2", "libelle_court": "Organisme nuisible 2", "libelle_long": "Organisme nuisible 1"},
            True,
        ),
        # Tester l'acceptation de valeurs différentes
        (
            {"code_oepp": "CODE2", "libelle_court": "Organisme nuisible 2", "libelle_long": "Organisme nuisible 2"},
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
    del fiche_detection.latest_version
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created

    latest_version = fiche_detection.latest_version
    lieu = LieuFactory(fiche_detection=fiche_detection, nom="Maison")
    del fiche_detection.latest_version
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created
    assert fiche_detection.latest_version.revision.comment == "Le lieu 'Maison' a été ajouté à la fiche"

    latest_version = fiche_detection.latest_version
    lieu.nom = "Nouvelle maison"
    lieu.save()
    del fiche_detection.latest_version
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created

    latest_version = fiche_detection.latest_version
    structure_sivep, _ = StructurePreleveuse.objects.get_or_create(nom="SIVEP")
    prelevement = PrelevementFactory(lieu=lieu, structure_preleveuse=structure_sivep)
    del fiche_detection.latest_version
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
    del fiche_detection.latest_version
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created

    latest_version = fiche_detection.latest_version
    prelevement.delete()
    del fiche_detection.latest_version
    assert latest_version.pk != fiche_detection.latest_version.pk
    assert latest_version.revision.date_created < fiche_detection.latest_version.revision.date_created
    assert (
        fiche_detection.latest_version.revision.comment
        == "Le prélèvement pour le lieu 'Nouvelle maison' et la structure 'SEMAE' a été supprimé de la fiche"
    )

    latest_version = fiche_detection.latest_version
    lieu.delete()
    del fiche_detection.latest_version
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

    del fiche_detection.latest_version
    with django_assert_num_queries(5):
        assert fiche_detection.latest_version is not None


@pytest.mark.django_db
def test_fiche_zone_delimitee_latest_revision():
    fiche_zone_delimitee = FicheZoneFactory()
    assert fiche_zone_delimitee.latest_version is not None
    latest_version = fiche_zone_delimitee.latest_version

    fiche_zone_delimitee.commentaire = "Lorem"
    fiche_zone_delimitee.save()
    del fiche_zone_delimitee.latest_version
    assert latest_version.pk != fiche_zone_delimitee.latest_version.pk
    assert latest_version.revision.date_created < fiche_zone_delimitee.latest_version.revision.date_created

    latest_version = fiche_zone_delimitee.latest_version
    zone_infestee = ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone_delimitee, nom="Zone 3")
    del fiche_zone_delimitee.latest_version
    assert latest_version.pk != fiche_zone_delimitee.latest_version.pk
    assert latest_version.revision.date_created < fiche_zone_delimitee.latest_version.revision.date_created
    assert fiche_zone_delimitee.latest_version.revision.comment == "La zone infestée 'Zone 3' a été ajoutée à la fiche"

    latest_version = fiche_zone_delimitee.latest_version
    zone_infestee.nom = "Zone 4"
    zone_infestee.save()
    del fiche_zone_delimitee.latest_version
    assert latest_version.pk != fiche_zone_delimitee.latest_version.pk
    assert latest_version.revision.date_created < fiche_zone_delimitee.latest_version.revision.date_created

    latest_version = fiche_zone_delimitee.latest_version
    zone_infestee.delete()
    del fiche_zone_delimitee.latest_version
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


@pytest.mark.django_db
def test_evenement_cant_be_limitee_without_structures():
    evenement = EvenementFactory()
    evenement.visibilite = Visibilite.LIMITEE

    with pytest.raises(ValidationError):
        evenement.save()


@pytest.mark.django_db
def test_evenement_can_be_limitee_with_structures():
    evenement = EvenementFactory()
    evenement.visibilite = Visibilite.LIMITEE
    evenement.allowed_structures.set(
        [
            StructureFactory(),
        ]
    )
    evenement.save()


@pytest.mark.django_db
def test_evenement_cant_be_national_with_structures():
    evenement = EvenementFactory()
    evenement.visibilite = Visibilite.NATIONALE
    evenement.allowed_structures.set(
        [
            StructureFactory(),
        ]
    )

    with pytest.raises(ValidationError):
        evenement.save()


@pytest.mark.django_db
def test_delete_fiche_zone_creates_revision_on_evenement():
    fiche_zone = FicheZoneFactory()
    ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone)
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone)
    latest_version = evenement.latest_version
    fiche_zone_id = fiche_zone.id
    zones_infestees = list(fiche_zone.zoneinfestee_set.all())

    fiche_zone.refresh_from_db()
    fiche_zone.delete()

    assert latest_version.pk != evenement.latest_version.pk
    assert latest_version.revision.date_created < evenement.latest_version.revision.date_created
    comment = evenement.latest_version.revision.comment

    assert comment.startswith(f"La fiche zone délimitée '{fiche_zone.evenement.numero}' a été supprimée.")
    version_fzd = VersionFicheZoneDelimitee.objects.filter(revision=evenement.latest_version.revision).first()
    data = version_fzd.fiche_zone_delimitee_data

    expected_data = {
        "id": fiche_zone_id,
        "createur": {
            "force_can_be_contacted": False,
            "id": fiche_zone.createur.id,
            "libelle": fiche_zone.createur.libelle,
            "niveau1": fiche_zone.createur.niveau1,
            "niveau2": fiche_zone.createur.niveau2,
        },
        "commentaire": fiche_zone.commentaire,
        "zones_infestees": [
            {
                "id": zone.id,
                "nom": zone.nom,
                "surface_infestee_totale": zone.surface_infestee_totale,
                "unite_surface_infestee_totale": zone.unite_surface_infestee_totale,
                "rayon": zone.rayon,
                "unite_rayon": zone.unite_rayon,
                "caracteristique_principale": zone.caracteristique_principale,
                "fiche_zone_delimitee": fiche_zone_id,
            }
            for zone in zones_infestees
        ],
        "rayon_zone_tampon": fiche_zone.rayon_zone_tampon,
        "surface_tampon_totale": fiche_zone.surface_tampon_totale,
        "unite_rayon_zone_tampon": fiche_zone.unite_rayon_zone_tampon,
        "unite_surface_tampon_totale": fiche_zone.unite_surface_tampon_totale,
    }

    assert data == expected_data


@pytest.mark.django_db
def test_siret_valid_14_digits():
    lieu = LieuFactory(siret_etablissement="12345678901234")
    lieu.full_clean()
    lieu.save()
    assert Lieu.objects.get(id=lieu.id).siret_etablissement == "12345678901234"


@pytest.mark.django_db
def test_siret_invalid_length():
    lieu = LieuFactory(siret_etablissement="123456789")
    with pytest.raises(ValidationError):
        lieu.full_clean()


def test_siret_invalid_characters():
    lieu = LieuFactory(siret_etablissement="123ABC45678901")
    with pytest.raises(ValidationError):
        lieu.full_clean()


@pytest.mark.django_db
def test_fiche_detection_numero():
    evenement = EvenementFactory()
    FicheDetectionFactory.create_batch(10, evenement=evenement)

    last_fiche = FicheDetectionFactory(evenement=evenement)
    assert last_fiche.numero_detection.endswith(".11")


@pytest.mark.django_db
def test_default_detection_order():
    evenement = EvenementFactory()
    detection_1 = FicheDetectionFactory(evenement=evenement, numero_detection="2")
    detection_2 = FicheDetectionFactory(evenement=evenement, numero_detection="1")
    detection_3 = FicheDetectionFactory(evenement=evenement, numero_detection="3")

    assert list(evenement.detections.all()) == [detection_2, detection_1, detection_3]


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_evenement_delete():
    evenement = EvenementFactory()
    date_derniere_mise_a_jour = evenement.date_derniere_mise_a_jour
    evenement.is_deleted = True
    evenement.save()
    assert date_derniere_mise_a_jour < evenement.date_derniere_mise_a_jour


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_fiche_detection_delete():
    fiche_detection = FicheDetectionFactory()
    date_derniere_mise_a_jour = fiche_detection.date_derniere_mise_a_jour

    fiche_detection.is_deleted = True
    fiche_detection.save()

    fiche_detection.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_detection.date_derniere_mise_a_jour


@pytest.mark.django_db
def test_cant_create_document_with_invalid_document_type():
    DocumentFactory(content_object=EvenementFactory(), document_type=Document.TypeDocument.ETIQUETAGE)
