import datetime

from django.db import IntegrityError
import pytest

from sa.tests.factories import AcarapioseFactory, AdenomatoseFactory, EvenementAnimalFactory, TuberculoseFactory


@pytest.mark.django_db
def test_evenement_animal_detenteur_constraint():
    EvenementAnimalFactory()
    EvenementAnimalFactory(particulier=True)

    with pytest.raises(IntegrityError):
        EvenementAnimalFactory(numero_identifiant_etablissement="Test", nom_particulier="Testeur")


@pytest.mark.django_db
def test_evenement_animal_numero():
    annee = datetime.date.today().year

    evenement = EvenementAnimalFactory(maladie=TuberculoseFactory(), numero_annee=None, numero_evenement=None)
    assert evenement.numero == f"TUB-{annee}.1"

    evenement = EvenementAnimalFactory(maladie=AcarapioseFactory(), numero_annee=None, numero_evenement=None)
    assert evenement.numero == f"DIV-{annee}.1"

    evenement = EvenementAnimalFactory(maladie=AdenomatoseFactory(), numero_annee=None, numero_evenement=None)
    assert evenement.numero == f"DIV-{annee}.2"
