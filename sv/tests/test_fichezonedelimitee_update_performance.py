from model_bakery import baker

from sv.factories import FicheZoneFactory, EvenementFactory
from sv.models import FicheDetection

BASE_NUM_QUERIES = 20


def test_update_fiche_zone_delimitee_form_with_multiple_existing_fiche_detection(
    client, django_assert_num_queries, mocked_authentification_user, fiche_zone_bakery
):
    """Vérifie l'évolution du nombre de requêtes SQL générées lors du chargement du formulaire de modification d'une zone délimitée,
    quel que soit le nombre de fiches de détection affichées dans les champs hors zone infestée et zone infestée"""
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    baker.make(
        FicheDetection,
        _fill_optional=True,
        createur=mocked_authentification_user.agent.structure,
        hors_zone_infestee=None,
        zone_infestee=None,
        evenement=evenement,
        _quantity=3,
    )
    client.get(fiche_zone_delimitee.get_update_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_zone_delimitee.get_update_url())

    baker.make(
        FicheDetection,
        _fill_optional=True,
        createur=mocked_authentification_user.agent.structure,
        hors_zone_infestee=None,
        zone_infestee=None,
        evenement=evenement,
        _quantity=3,
    )
    with django_assert_num_queries(BASE_NUM_QUERIES + 3):
        client.get(fiche_zone_delimitee.get_update_url())
