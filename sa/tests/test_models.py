from django.db import IntegrityError
import pytest

from sa.tests.factories import EvenementAnimalFactory


@pytest.mark.django_db
def test_evenement_animal_detenteur_constraint():
    EvenementAnimalFactory()
    EvenementAnimalFactory(particulier=True)

    with pytest.raises(IntegrityError):
        EvenementAnimalFactory(numero_identifiant_etablissement="Test", nom_particulier="Testeur")
