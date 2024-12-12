import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from model_bakery import baker
from django.db.utils import IntegrityError

from core.models import Visibilite
from sv.constants import STRUCTURE_EXPLOITANT
from sv.models import (
    FicheZoneDelimitee,
    ZoneInfestee,
    FicheDetection,
    Etat,
    Lieu,
    StructurePreleveuse,
    Prelevement,
    LaboratoireAgree,
    LaboratoireConfirmationOfficielle,
)


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
    base_data = {
        "is_officiel": False,
        "lieu": baker.make(Lieu),
        "resultat": Prelevement.Resultat.DETECTE,
        "structure_preleveuse": baker.make(StructurePreleveuse),
    }

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Prelevement.objects.create(**base_data, numero_rapport_inspection="Foo")

    labo = baker.make(LaboratoireAgree)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Prelevement.objects.create(**base_data, laboratoire_agree=labo)

    labo = baker.make(LaboratoireConfirmationOfficielle)
    with pytest.raises(IntegrityError):
        Prelevement.objects.create(**base_data, laboratoire_confirmation_officielle=labo)


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
