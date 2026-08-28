import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone
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


@pytest.mark.django_db
def test_evenement_animal_dates_mesures_constraints():
    today = timezone.localtime(timezone.now()).date()

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EvenementAnimalFactory(
                maladie__needs_dates_desinfection=True, date_d_zero=today + datetime.timedelta(days=3), date_nd1=today
            )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EvenementAnimalFactory(
                maladie__needs_dates_desinfection=True, date_nd1=today + datetime.timedelta(days=3), date_nd2=today
            )
