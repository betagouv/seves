from django.urls import reverse

from model_bakery import baker

from core.models import Visibilite
from sv.forms import RattachementChoices
from sv.models import Etat, OrganismeNuisible, FicheDetection

BASE_NUM_QUERIES = 7


def test_add_fiche_zone_delimitee_form_with_multiple_existing_fiche_detection(
    client, django_assert_num_queries, mocked_authentification_user
):
    """Vérifie que le nombre de requêtes SQL générées lors du chargement du formulaire de création d'une zone délimitée reste constant,
    quel que soit le nombre de fiches de détection affichées dans les champs hors zone infestée et zone infestée"""
    organisme_nuisible = baker.make(OrganismeNuisible)
    etat = Etat.objects.get(id=Etat.get_etat_initial())
    detections = baker.make(
        FicheDetection,
        _fill_optional=True,
        etat=etat,
        createur=mocked_authentification_user.agent.structure,
        hors_zone_infestee=None,
        zone_infestee=None,
        organisme_nuisible=organisme_nuisible,
        visibilite=Visibilite.LOCAL,
        _quantity=3,
    )
    url = f"{reverse('fiche-zone-delimitee-creation')}?fiche_detection_id={detections[0].pk}&rattachement={RattachementChoices.HORS_ZONE_INFESTEE}"
    client.get(url)

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(url)

    baker.make(
        FicheDetection,
        _fill_optional=True,
        etat=etat,
        createur=mocked_authentification_user.agent.structure,
        hors_zone_infestee=None,
        zone_infestee=None,
        organisme_nuisible=organisme_nuisible,
        visibilite=Visibilite.LOCAL,
        _quantity=3,
    )
    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(url)
