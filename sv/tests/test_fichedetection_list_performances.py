import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_list_performance(client, django_assert_num_queries, mocked_authentification_user, fiche_detection_bakery):
    fiche_detection_bakery()
    client.get(reverse("fiche-detection-list"))

    with django_assert_num_queries(9):
        client.get(reverse("fiche-detection-list"))

    for _ in range(0, 5):
        fiche_detection_bakery()

    with django_assert_num_queries(9):
        client.get(reverse("fiche-detection-list"))
