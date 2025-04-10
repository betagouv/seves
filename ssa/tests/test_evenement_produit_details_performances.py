from ssa.factories import EvenementProduitFactory, EtablissementFactory


def test_evenement_produit_performances(client, django_assert_num_queries):
    evenement = EvenementProduitFactory()
    client.get(evenement.get_absolute_url())

    with django_assert_num_queries(5):
        client.get(evenement.get_absolute_url())

    EtablissementFactory(evenement_produit=evenement)

    with django_assert_num_queries(7):
        client.get(evenement.get_absolute_url())

    EtablissementFactory.create_batch(3, evenement_produit=evenement)

    with django_assert_num_queries(6):
        client.get(evenement.get_absolute_url())
