import pytest

from sv.factories import FicheDetectionFactory, FicheZoneFactory, ZoneInfesteeFactory
from sv.models import FicheZoneDelimitee


@pytest.mark.django_db
def test_with_nb_fiches_detection():
    fiche_zone = FicheZoneFactory()
    assert FicheZoneDelimitee
    assert FicheZoneDelimitee.objects.all().with_nb_fiches_detection().get().nb_fiches_detection == 0

    FicheDetectionFactory()
    assert FicheZoneDelimitee.objects.all().with_nb_fiches_detection().get().nb_fiches_detection == 0

    FicheDetectionFactory(hors_zone_infestee=fiche_zone)
    assert FicheZoneDelimitee.objects.all().with_nb_fiches_detection().get().nb_fiches_detection == 1

    zone_infesteee = ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone)
    FicheDetectionFactory.create_batch(2, zone_infestee=zone_infesteee)

    assert FicheZoneDelimitee.objects.all().with_nb_fiches_detection().get().nb_fiches_detection == 3

    zone_infesteee = ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone)
    FicheDetectionFactory(zone_infestee=zone_infesteee)

    assert FicheZoneDelimitee.objects.all().with_nb_fiches_detection().get().nb_fiches_detection == 4
