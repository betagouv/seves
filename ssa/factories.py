import random
from datetime import datetime

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from core.factories import BaseEtablissementFactory
from core.models import Structure
from ssa.models import (
    EvenementProduit,
    TypeEvenement,
    Source,
    TemperatureConservation,
    QuantificationUnite,
    ActionEngagees,
    Etablissement,
    PositionDossier,
    CategorieDanger,
)
from ssa.models.evenement_produit import PretAManger, CategorieProduit


def generate_rappel_conso():
    return f"{random.randint(2000, 2030)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"


class EvenementProduitFactory(DjangoModelFactory):
    class Meta:
        model = EvenementProduit

    date_creation = factory.Faker("date_time_this_decade")
    date_reception = factory.Faker("date_this_decade")
    numero_annee = factory.Faker("year")
    numero_rasff = factory.Faker("bothify", text="####.####")
    type_evenement = FuzzyChoice([choice[0] for choice in TypeEvenement.choices])
    source = FuzzyChoice(Source.values)
    description = factory.Faker("paragraph")
    aliments_animaux = factory.Faker("boolean")

    categorie_produit = FuzzyChoice(CategorieProduit.values)
    denomination = factory.Faker("sentence", nb_words=5)
    marque = factory.Faker("sentence", nb_words=5)
    lots = factory.Faker("paragraph")
    description_complementaire = factory.Faker("paragraph")
    temperature_conservation = FuzzyChoice([choice[0] for choice in TemperatureConservation.choices])

    categorie_danger = FuzzyChoice(CategorieDanger.values)
    precision_danger = factory.Faker("sentence", nb_words=3)
    quantification = factory.Faker("sentence", nb_words=1)
    quantification_unite = FuzzyChoice([choice[0] for choice in QuantificationUnite.choices])
    evaluation = factory.Faker("paragraph")
    reference_souches = factory.Faker("sentence", nb_words=5)
    reference_clusters = factory.Faker("sentence", nb_words=5)

    actions_engagees = FuzzyChoice([choice[0] for choice in ActionEngagees.choices])

    numeros_rappel_conso = factory.LazyAttribute(
        lambda x: [generate_rappel_conso() for _ in range(random.randint(0, 5))]
    )

    @factory.lazy_attribute
    def createur(self):
        return Structure.objects.get(libelle="Structure Test")

    @factory.post_generation
    def date_creation(self, create, extracted, **kwargs):  # noqa: F811
        if extracted and create:
            if isinstance(extracted, str):
                self.date_creation = timezone.make_aware(datetime.strptime(extracted, "%Y-%m-%d"))
            else:
                self.date_creation = extracted
            self.save()

    @factory.lazy_attribute
    def produit_pret_a_manger(self):
        if self.categorie_danger in CategorieDanger.dangers_bacteriens():
            return random.choice(PretAManger.values)
        return ""

    @factory.sequence
    def numero_evenement(n):
        return n + 1

    class Params:
        not_bacterie = factory.Trait(
            categorie_danger=factory.LazyAttribute(
                lambda _: random.choice(
                    [c[0] for c in CategorieDanger.choices if c[0] not in CategorieDanger.dangers_bacteriens()]
                )
            )
        )
        bacterie = factory.Trait(
            categorie_danger=factory.LazyAttribute(
                lambda _: random.choice(
                    [c[0] for c in CategorieDanger.choices if c[0] in CategorieDanger.dangers_bacteriens()]
                )
            )
        )


class EtablissementFactory(BaseEtablissementFactory, DjangoModelFactory):
    class Meta:
        model = Etablissement

    evenement_produit = factory.SubFactory("ssa.factories.EvenementProduitFactory")

    position_dossier = FuzzyChoice([choice[0] for choice in PositionDossier.choices])
    type_exploitant = factory.Faker("sentence", nb_words=2)
    numero_agrement = factory.Faker("numerify", text="###.##.###")

    numeros_resytal = factory.Faker("numerify", text="######")
