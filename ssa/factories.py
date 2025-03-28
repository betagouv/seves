from datetime import datetime

from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyFloat

from core.models import Structure
from ssa.models import (
    EvenementProduit,
    TypeEvenement,
    CerfaRecu,
    Source,
    TemperatureConservation,
    QuantificationUnite,
    ActionEngagees,
)
import factory

from ssa.models.evenement_produit import PretAManger


class EvenementProduitFactory(DjangoModelFactory):
    class Meta:
        model = EvenementProduit

    date_creation = factory.Faker("date_this_decade")
    numero_annee = factory.Faker("year")
    numero_evenement = factory.Faker("pyint", min_value=0, max_value=1000)
    numero_rasff = factory.Faker("bothify", text="#?#?#?#?#")
    type_evenement = FuzzyChoice([choice[0] for choice in TypeEvenement.choices])
    source = FuzzyChoice([choice[0] for choice in Source.choices])
    cerfa_recu = FuzzyChoice([choice[0] for choice in CerfaRecu.choices])
    description = factory.Faker("paragraph")

    denomination = factory.Faker("sentence", nb_words=5)
    marque = factory.Faker("sentence", nb_words=5)
    lots = factory.Faker("paragraph")
    description_complementaire = factory.Faker("paragraph")
    temperature_conservation = FuzzyChoice([choice[0] for choice in TemperatureConservation.choices])
    produit_pret_a_manger = FuzzyChoice([choice[0] for choice in PretAManger.choices])

    quantification = FuzzyFloat(low=0, precision=2)
    quantification_unite = FuzzyChoice([choice[0] for choice in QuantificationUnite.choices])
    evaluation = factory.Faker("paragraph")
    reference_souches = factory.Faker("sentence", nb_words=5)
    reference_clusters = factory.Faker("sentence", nb_words=5)

    actions_engagees = FuzzyChoice([choice[0] for choice in ActionEngagees.choices])

    @factory.lazy_attribute
    def createur(self):
        return Structure.objects.get(libelle="Structure Test")

    @factory.post_generation
    def date_creation(self, create, extracted, **kwargs):  # noqa: F811
        if extracted and create:
            if isinstance(extracted, str):
                self.date_creation = datetime.strptime(extracted, "%Y-%m-%d").date()
            else:
                self.date_creation = extracted
            self.save()
