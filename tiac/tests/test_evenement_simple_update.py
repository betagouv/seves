import pytest
from django.urls import reverse

from tiac.factories import EvenementSimpleFactory


@pytest.mark.django_db
def test_update_evenement_simple_performances(client, django_assert_num_queries):
    evenement = EvenementSimpleFactory()

    with django_assert_num_queries(12):
        client.get(reverse("tiac:evenement-simple-edition", kwargs={"pk": evenement.pk}))
