from sv.factories import FicheZoneFactory, EvenementFactory, FicheDetectionFactory

BASE_NUM_QUERIES = 13


def test_update_fiche_zone_delimitee_form_with_multiple_existing_fiche_detection(
    client, django_assert_num_queries, mocked_authentification_user
):
    """Vérifie l'évolution du nombre de requêtes SQL générées lors du chargement du formulaire de modification d'une zone délimitée,
    quel que soit le nombre de fiches de détection affichées dans les champs hors zone infestée et zone infestée"""
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    FicheDetectionFactory.create_batch(3, evenement=evenement)
    client.get(fiche_zone_delimitee.get_update_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_zone_delimitee.get_update_url())

    FicheDetectionFactory.create_batch(3, evenement=evenement)
    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_zone_delimitee.get_update_url())
