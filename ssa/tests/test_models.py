import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit, TypeEvenement, Source


@pytest.mark.django_db
def test_numero_rappel_conso():
    evenement = EvenementProduitFactory(numeros_rappel_conso=["1999-01-0123"])
    evenement.full_clean()

    evenement = EvenementProduitFactory(numeros_rappel_conso=["1999-01-3"])
    with pytest.raises(ValidationError):
        evenement.full_clean()

    evenement = EvenementProduitFactory(numeros_rappel_conso=["1999-1-3333"])
    with pytest.raises(ValidationError):
        evenement.full_clean()


@pytest.mark.django_db
def test_type_evenement_source_constraint():
    # Autre can be used for any type
    EvenementProduitFactory(type_evenement=TypeEvenement.ALERTE_PRODUIT_NATIONALE, source=Source.AUTRE)
    EvenementProduitFactory(type_evenement=TypeEvenement.INVESTIGATION_CAS_HUMAINS, source=Source.AUTRE)

    # Non human case can have sources, but not any of SOURCES_FOR_HUMAN_CASE
    EvenementProduitFactory(type_evenement=TypeEvenement.ALERTE_PRODUIT_NATIONALE, source=Source.AUTOCONTROLE)
    for source in EvenementProduit.SOURCES_FOR_HUMAN_CASE:
        with pytest.raises(IntegrityError):
            EvenementProduitFactory(type_evenement=TypeEvenement.ALERTE_PRODUIT_NATIONALE, source=source)

    # Human case can have sources, but only of SOURCES_FOR_HUMAN_CASE
    for source in EvenementProduit.SOURCES_FOR_HUMAN_CASE:
        EvenementProduitFactory(type_evenement=TypeEvenement.INVESTIGATION_CAS_HUMAINS, source=source)

    with pytest.raises(IntegrityError):
        EvenementProduitFactory(type_evenement=TypeEvenement.INVESTIGATION_CAS_HUMAINS, source=Source.AUTOCONTROLE)
