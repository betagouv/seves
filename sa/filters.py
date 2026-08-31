import django_filters
from dsfr.forms import DsfrBaseForm

from core.filters_mixins import WithEtatFilterMixin, WithNumeroFilterMixin
from seves import settings

from .models import Espece, EvenementAnimal, Maladie


class EvenementAnimalFilterForm(DsfrBaseForm):
    pass


class EvenementAnimalFilter(
    WithNumeroFilterMixin,
    WithEtatFilterMixin,
    django_filters.FilterSet,
):
    maladie = django_filters.ModelChoiceFilter(
        label="Maladie",
        queryset=Maladie.objects.all(),
        empty_label=settings.SELECT_EMPTY_CHOICE,
    )
    espece = django_filters.ModelChoiceFilter(
        label="Espèce",
        queryset=Espece.objects.all(),
        empty_label=settings.SELECT_EMPTY_CHOICE,
    )

    class Meta:
        model = EvenementAnimal
        fields = ["annee", "numero", "maladie", "espece", "etat"]
        form = EvenementAnimalFilterForm
