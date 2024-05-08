import pytest
from model_bakery import baker
from django.db.utils import IntegrityError
from sv.models import FicheZoneDelimitee, ZoneInfestee, FicheDetection


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
