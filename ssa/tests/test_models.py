from django.core.exceptions import ValidationError

from ssa.factories import EvenementProduitFactory
import pytest


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
