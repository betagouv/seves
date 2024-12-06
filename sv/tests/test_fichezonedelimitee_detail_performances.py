from model_bakery import baker
from sv.models import FicheDetection, ZoneInfestee

BASE_NUM_QUERIES = 13


def test_empty_fiche_zone_delimitee_performances(
    client, django_assert_num_queries, fiche_zone, mocked_authentification_user
):
    client.get(fiche_zone.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_zone.get_absolute_url())


def test_fiche_zone_delimitee_with_one_detection_in_hors_zone_infestee(
    client, fiche_zone, django_assert_num_queries, mocked_authentification_user
):
    baker.make(FicheDetection, hors_zone_infestee=fiche_zone)
    client.get(fiche_zone.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_zone.get_absolute_url())


def test_fiche_zone_delimitee_with_multiple_detection_in_hors_zone_infestee(
    client, fiche_zone, django_assert_num_queries, mocked_authentification_user
):
    baker.make(FicheDetection, hors_zone_infestee=fiche_zone, _quantity=3)

    client.get(fiche_zone.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_zone.get_absolute_url())


def test_fiche_zone_delimitee_with_one_zone_infestee(
    client, django_assert_num_queries, fiche_zone, mocked_authentification_user
):
    zone_infestee = baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone)
    baker.make(FicheDetection, zone_infestee=zone_infestee)

    client.get(fiche_zone.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES + 1):
        client.get(fiche_zone.get_absolute_url())


def test_fiche_zone_delimitee_with_multiple_zone_infestee(
    client, fiche_zone, django_assert_num_queries, mocked_authentification_user
):
    zones_infestees = [baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone) for _ in range(4)]
    for zone_infestee in zones_infestees:
        baker.make(FicheDetection, zone_infestee=zone_infestee)

    client.get(fiche_zone.get_absolute_url())

    with django_assert_num_queries(BASE_NUM_QUERIES + 1):
        client.get(fiche_zone.get_absolute_url())
