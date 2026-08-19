import datetime

from django.db import IntegrityError, transaction
import pytest

from sa.models.evenement import StatutAnimal, TypeLieu
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


@pytest.mark.django_db
def test_evenement_animal_type_lieu_consistent_with_statut_animal_constraint():
    EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU, type_lieu=TypeLieu.SLAUGHTERHOUSE)
    EvenementAnimalFactory(statut_animal=StatutAnimal.SAUVAGE, type_lieu=TypeLieu.FOREST)

    with transaction.atomic(), pytest.raises(IntegrityError):
        EvenementAnimalFactory(statut_animal=StatutAnimal.SAUVAGE, type_lieu=TypeLieu.SLAUGHTERHOUSE)

    with transaction.atomic(), pytest.raises(IntegrityError):
        EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU, type_lieu=TypeLieu.FOREST)
