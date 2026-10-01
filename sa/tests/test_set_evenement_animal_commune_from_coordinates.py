from unittest import mock

from django.core.management import call_command

from core.factories import DepartementFactory
from sa.tests.factories import EvenementAnimalFactory


def _mock_geo_api(communes):
    response = mock.Mock()
    response.json.return_value = communes
    return mock.patch("requests.get", return_value=response)


def test_sets_commune_and_departement_from_coordinates(db):
    departement = DepartementFactory(numero="59", nom="Nord")
    evenement = EvenementAnimalFactory(commune="", code_insee="", departement=None)

    with _mock_geo_api([{"nom": "Lille", "code": "59350", "departement": {"code": "59", "nom": "Nord"}}]) as get:
        call_command("set_evenement_animal_commune_from_coordinates")

    get.assert_called_once()
    assert get.call_args.kwargs["params"]["lat"] == evenement.coordinates.y
    assert get.call_args.kwargs["params"]["lon"] == evenement.coordinates.x
    evenement.refresh_from_db()
    assert evenement.commune == "Lille"
    assert evenement.code_insee == "59350"
    assert evenement.departement == departement


def test_sets_departement_from_existing_code_insee_without_calling_api(db):
    departement = DepartementFactory(numero="2A", nom="Corse-du-Sud")
    evenement = EvenementAnimalFactory(commune="Ajaccio", code_insee="2A004", departement=None)

    with _mock_geo_api([]) as get:
        call_command("set_evenement_animal_commune_from_coordinates")

    get.assert_not_called()
    evenement.refresh_from_db()
    assert evenement.commune == "Ajaccio"
    assert evenement.departement == departement


def test_leaves_evenement_untouched_when_no_commune_found(db):
    evenement = EvenementAnimalFactory(commune="", code_insee="", departement=None)

    with _mock_geo_api([]):
        call_command("set_evenement_animal_commune_from_coordinates")

    evenement.refresh_from_db()
    assert evenement.commune == ""
    assert evenement.departement is None


def test_ignores_evenement_already_complete(db):
    EvenementAnimalFactory()

    with _mock_geo_api([]) as get:
        call_command("set_evenement_animal_commune_from_coordinates")

    get.assert_not_called()
