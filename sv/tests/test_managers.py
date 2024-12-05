import pytest
from model_bakery import baker

from sv.models import FicheZoneDelimitee, ZoneInfestee


@pytest.mark.django_db
def test_with_nb_fiches_detection(fiche_detection_bakery, fiche_zone):
    assert FicheZoneDelimitee.objects.all().with_nb_fiches_detection().get().nb_fiches_detection == 0

    fiche_detection_bakery()
    assert FicheZoneDelimitee.objects.all().with_nb_fiches_detection().get().nb_fiches_detection == 0

    detection = fiche_detection_bakery()
    detection.hors_zone_infestee = fiche_zone
    detection.save()
    assert FicheZoneDelimitee.objects.all().with_nb_fiches_detection().get().nb_fiches_detection == 1

    zone_infestee = baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone)
    for _ in range(2):
        detection = fiche_detection_bakery()
        detection.zone_infestee = zone_infestee
        detection.save()

    assert FicheZoneDelimitee.objects.all().with_nb_fiches_detection().get().nb_fiches_detection == 3

    zone_infestee = baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone)
    detection = fiche_detection_bakery()
    detection.zone_infestee = zone_infestee
    detection.save()

    assert FicheZoneDelimitee.objects.all().with_nb_fiches_detection().get().nb_fiches_detection == 4
