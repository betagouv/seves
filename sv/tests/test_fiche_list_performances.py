import pytest
from django.urls import reverse

from sv.factories import EvenementFactory, FicheDetectionFactory, FicheZoneFactory


@pytest.mark.django_db
def test_list_detection_performance(client, django_assert_num_queries, mocked_authentification_user):
    FicheDetectionFactory()
    client.get(reverse("fiche-liste"))

    with django_assert_num_queries(7):
        client.get(reverse("fiche-liste"))

    for _ in range(0, 5):
        FicheDetectionFactory()

    with django_assert_num_queries(7):
        client.get(reverse("fiche-liste"))


@pytest.mark.django_db
def test_list_zone_performance(client, django_assert_num_queries, mocked_authentification_user):
    EvenementFactory(fiche_zone_delimitee=FicheZoneFactory())
    url = reverse("fiche-liste") + "?type_fiche=zone"
    client.get(url)

    with django_assert_num_queries(6):
        client.get(url)

    for _ in range(0, 5):
        EvenementFactory(fiche_zone_delimitee=FicheZoneFactory())

    with django_assert_num_queries(6):
        client.get(url)
