from core.models import LienLibre
from ssa.factories import EvenementProduitFactory, EtablissementFactory

NUMBER_BASE_QUERIES = 9


def test_evenement_produit_performances(client, django_assert_num_queries):
    evenement = EvenementProduitFactory()
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(NUMBER_BASE_QUERIES):
        client.get(evenement.get_absolute_url())

    EtablissementFactory(evenement_produit=evenement)

    with django_assert_num_queries(NUMBER_BASE_QUERIES + 2):
        client.get(evenement.get_absolute_url())

    EtablissementFactory.create_batch(3, evenement_produit=evenement)

    with django_assert_num_queries(NUMBER_BASE_QUERIES + 2):
        client.get(evenement.get_absolute_url())


def test_evenement_produit_performances_with_free_links(client, django_assert_num_queries):
    evenement = EvenementProduitFactory()
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(NUMBER_BASE_QUERIES):
        client.get(evenement.get_absolute_url())

    LienLibre.objects.create(related_object_1=evenement, related_object_2=EvenementProduitFactory())
    LienLibre.objects.create(related_object_1=evenement, related_object_2=EvenementProduitFactory())
    LienLibre.objects.create(related_object_1=evenement, related_object_2=EvenementProduitFactory())

    with django_assert_num_queries(NUMBER_BASE_QUERIES + 6):
        client.get(evenement.get_absolute_url())
