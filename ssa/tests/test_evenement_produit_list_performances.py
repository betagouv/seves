from django.urls import reverse
from playwright.sync_api import Page

from core.models import LienLibre
from ssa.factories import EvenementProduitFactory

NB_QUERIES = 14


def test_list_performances(live_server, mocked_authentification_user, page: Page, django_assert_num_queries, client):
    EvenementProduitFactory()
    url = reverse("ssa:evenements-liste")
    with django_assert_num_queries(NB_QUERIES):
        client.get(url)

    EvenementProduitFactory.create_batch(4)
    with django_assert_num_queries(NB_QUERIES - 1):
        client.get(url)


def test_list_performances_with_free_links(
    live_server, mocked_authentification_user, page: Page, django_assert_num_queries, client
):
    evenement = EvenementProduitFactory()
    url = reverse("ssa:evenements-liste")
    with django_assert_num_queries(NB_QUERIES):
        client.get(url)

    LienLibre.objects.create(related_object_1=evenement, related_object_2=EvenementProduitFactory())
    LienLibre.objects.create(related_object_1=evenement, related_object_2=EvenementProduitFactory())
    LienLibre.objects.create(related_object_1=evenement, related_object_2=EvenementProduitFactory())
    with django_assert_num_queries(NB_QUERIES - 1):
        client.get(url)
