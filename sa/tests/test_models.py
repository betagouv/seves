import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone
import pytest

from sa.models import Maladie
from sa.models.evenement import StatutAnimal, TypeLieu
from sa.tests.factories import (
    AcarapioseFactory,
    AdenomatoseFactory,
    EvenementAnimalFactory,
    TuberculoseFactory,
    TypageFactory,
)


@pytest.mark.django_db
def test_evenement_animal_detenteur_constraint():
    EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU)
    EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU, particulier=True)

    with pytest.raises(IntegrityError):
        EvenementAnimalFactory(
            statut_animal=StatutAnimal.DETENU, numero_identifiant_etablissement="Test", nom_particulier="Testeur"
        )


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
    EvenementAnimalFactory(statut_animal=StatutAnimal.SAUVAGE, type_lieu=TypeLieu.SHELLFISH_BED)

    with transaction.atomic(), pytest.raises(IntegrityError):
        EvenementAnimalFactory(statut_animal=StatutAnimal.SAUVAGE, type_lieu=TypeLieu.SLAUGHTERHOUSE)

    with transaction.atomic(), pytest.raises(IntegrityError):
        EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU, type_lieu=TypeLieu.SHELLFISH_BED)


@pytest.mark.django_db
def test_evenement_animal_dates_mesures_constraints():
    today = timezone.localtime(timezone.now()).date()

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EvenementAnimalFactory(
                statut_animal=StatutAnimal.DETENU,
                maladie__needs_dates_desinfection=True,
                date_d_zero=today + datetime.timedelta(days=3),
                date_nd1=today,
            )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EvenementAnimalFactory(
                statut_animal=StatutAnimal.DETENU,
                maladie__needs_dates_desinfection=True,
                date_nd1=today + datetime.timedelta(days=3),
                date_nd2=today,
            )


@pytest.mark.django_db
def test_evenement_animal_no_mesures_gestion_when_sauvage_constraint():
    today = timezone.localtime(timezone.now()).date()
    maladie = TuberculoseFactory()

    EvenementAnimalFactory(statut_animal=StatutAnimal.SAUVAGE, maladie=maladie)
    EvenementAnimalFactory(statut_animal=StatutAnimal.DETENU, maladie=maladie, date_apms=today, date_nd=today)

    for field in ("date_apms", "date_apdi", "date_levee", "date_d_zero", "date_nd1", "date_nd2", "date_nd"):
        with transaction.atomic(), pytest.raises(IntegrityError):
            EvenementAnimalFactory(statut_animal=StatutAnimal.SAUVAGE, maladie=maladie, **{field: today})


@pytest.mark.django_db
def test_maladie_treeselect_choices_with_typages_are_sorted_numerically():
    maladie = TuberculoseFactory()
    maladie.typages.all().delete()
    for valeur_niveau_2, valeur_niveau_3 in [
        ("PTV-10", ""),
        ("PTV-2", ""),
        ("PTV-1", "H10N1"),
        ("PTV-1", "H2N1"),
        ("PTV-1", "H1N10"),
        ("PTV-1", "H1N2"),
    ]:
        TypageFactory(maladie=maladie, valeur_niveau_2=valeur_niveau_2, valeur_niveau_3=valeur_niveau_3)

    maladie_choice = next(
        choice for group in Maladie.treeselect_choices_with_typages for choice in group if choice.value == maladie.pk
    )

    assert [choice.label for choice in maladie_choice] == ["PTV-1", "PTV-2", "PTV-10"]
    assert [choice.label for choice in maladie_choice[0]] == ["H1N2", "H1N10", "H2N1", "H10N1"]
