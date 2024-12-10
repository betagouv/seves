import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker
from django.db.utils import IntegrityError

from core.models import Visibilite
from sv.models import FicheZoneDelimitee, ZoneInfestee, FicheDetection, Etat, Lieu


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
