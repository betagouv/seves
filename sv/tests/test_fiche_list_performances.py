import pytest
from django.urls import reverse

from sv.factories import EvenementFactory, FicheDetectionFactory, FicheZoneFactory


@pytest.mark.django_db
def test_list_detection_performance(client, django_assert_num_queries, mocked_authentification_user):
    FicheDetectionFactory()
    client.get(reverse("sv:evenement-liste"))

    with django_assert_num_queries(15):
        client.get(reverse("sv:evenement-liste"))

    for _ in range(0, 5):
        FicheDetectionFactory()

    with django_assert_num_queries(15):
        client.get(reverse("sv:evenement-liste"))


@pytest.mark.django_db
def test_list_zone_performance(client, django_assert_num_queries, mocked_authentification_user):
    EvenementFactory(fiche_zone_delimitee=FicheZoneFactory())
    url = reverse("sv:evenement-liste")
    client.get(url)

    with django_assert_num_queries(14):
        client.get(url)

    for _ in range(0, 5):
        EvenementFactory(fiche_zone_delimitee=FicheZoneFactory())

    with django_assert_num_queries(14):
        client.get(url)
