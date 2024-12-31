import pytest
from model_bakery import baker

from core.models import Visibilite
from sv.models import Etat, OrganismeNuisible, FicheDetection

BASE_NUM_QUERIES = 13


@pytest.mark.skip(reason="refacto evenement")
def test_update_fiche_zone_delimitee_form_with_multiple_existing_fiche_detection(
    client, django_assert_num_queries, mocked_authentification_user, fiche_zone_bakery
):
    """Vérifie que le nombre de requêtes SQL générées lors du chargement du formulaire de modification d'une zone délimitée reste constant,
    quel que soit le nombre de fiches de détection affichées dans les champs hors zone infestée et zone infestée"""
    organisme_nuisible = baker.make(OrganismeNuisible)
    etat = Etat.objects.get(id=Etat.get_etat_initial())
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
    fiche_zone_delimitee = fiche_zone_bakery()
    fiche_zone_delimitee.organisme_nuisible = organisme_nuisible
    fiche_zone_delimitee.save()
    client.get(fiche_zone_delimitee.get_update_url())

    with django_assert_num_queries(BASE_NUM_QUERIES):
        client.get(fiche_zone_delimitee.get_update_url())

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
        client.get(fiche_zone_delimitee.get_update_url())
