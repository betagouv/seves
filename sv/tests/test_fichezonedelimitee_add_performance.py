from django.urls import reverse

from sv.factories import EvenementFactory, FicheDetectionFactory

BASE_NUM_QUERIES = 5


def test_add_fiche_zone_delimitee_form_with_multiple_existing_fiche_detection(
    client, django_assert_num_queries, mocked_authentification_user
):
    """Vérifie le nombre de requêtes SQL générées lors du chargement du formulaire de création d'une zone délimitée,
    en fonction du nombre de fiches de détection affichées dans les champs hors zone infestée et zone infestée"""
    evenement = EvenementFactory()
    FicheDetectionFactory(evenement=evenement)

    url = f"{reverse('sv:fiche-zone-delimitee-creation')}?evenement={evenement.pk}"
    client.get(url)

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(url)

    FicheDetectionFactory.create_batch(3, evenement=evenement)
    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(url)
