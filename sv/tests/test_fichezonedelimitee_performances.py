from model_bakery import baker
from sv.models import FicheZoneDelimitee, FicheDetection, ZoneInfestee

BASE_NUM_QUERIES = 6


def test_empty_fiche_zone_delimitee_performances(client, django_assert_num_queries, mocked_authentification_user):
    fiche = baker.make(FicheZoneDelimitee, createur=mocked_authentification_user.agent.structure, _fill_optional=True)

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche.get_absolute_url())


def test_fiche_zone_delimitee_with_one_detection_in_hors_zone_infestee(
    client, django_assert_num_queries, mocked_authentification_user
):
    fiche = baker.make(FicheZoneDelimitee, createur=mocked_authentification_user.agent.structure, _fill_optional=True)
    baker.make(FicheDetection, hors_zone_infestee=fiche)

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche.get_absolute_url())


def test_fiche_zone_delimitee_with_multiple_detection_in_hors_zone_infestee(
    client, django_assert_num_queries, mocked_authentification_user
):
    fiche = baker.make(FicheZoneDelimitee, createur=mocked_authentification_user.agent.structure, _fill_optional=True)
    baker.make(FicheDetection, hors_zone_infestee=fiche, _quantity=3)

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche.get_absolute_url())


def test_fiche_zone_delimitee_with_one_zone_infestee(client, django_assert_num_queries, mocked_authentification_user):
    fiche = baker.make(FicheZoneDelimitee, createur=mocked_authentification_user.agent.structure, _fill_optional=True)
    zone_infestee = baker.make(ZoneInfestee, fiche_zone_delimitee=fiche)
    baker.make(FicheDetection, zone_infestee=zone_infestee)

    with django_assert_num_queries(BASE_NUM_QUERIES + 2):
        client.get(fiche.get_absolute_url())


def test_fiche_zone_delimitee_with_multiple_zone_infestee(
    client, django_assert_num_queries, mocked_authentification_user
):
    fiche = baker.make(FicheZoneDelimitee, createur=mocked_authentification_user.agent.structure, _fill_optional=True)
    zones_infestees = [baker.make(ZoneInfestee, fiche_zone_delimitee=fiche) for _ in range(4)]
    for zone_infestee in zones_infestees:
        baker.make(FicheDetection, zone_infestee=zone_infestee)

    with django_assert_num_queries(BASE_NUM_QUERIES + 2):
        client.get(fiche.get_absolute_url())
