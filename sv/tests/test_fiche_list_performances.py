import pytest
from django.urls import reverse

from sv.factories import EvenementFactory


@pytest.mark.django_db
def test_list_detection_performance(
    client, django_assert_num_queries, mocked_authentification_user, fiche_detection_bakery
):
    fiche_detection_bakery()
    client.get(reverse("fiche-liste"))

    with django_assert_num_queries(6):
        client.get(reverse("fiche-liste"))

    for _ in range(0, 5):
        fiche_detection_bakery()

    with django_assert_num_queries(6):
        client.get(reverse("fiche-liste"))


@pytest.mark.django_db
def test_list_zone_performance(client, django_assert_num_queries, mocked_authentification_user, fiche_zone_bakery):
    EvenementFactory(fiche_zone_delimitee=fiche_zone_bakery())
    url = reverse("fiche-liste") + "?type_fiche=zone"
    client.get(url)

    with django_assert_num_queries(5):
        client.get(url)

    for _ in range(0, 5):
        EvenementFactory(fiche_zone_delimitee=fiche_zone_bakery())

    with django_assert_num_queries(5):
        client.get(url)
