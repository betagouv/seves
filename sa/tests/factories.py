from django.contrib.gis.geos import Point
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from faker import Faker

from core.models import Structure
from sa.models import Espece, EvenementAnimal, Maladie
from sa.models.evenement import ContexteSuspicion, HumanInvolved, StatutAnimal, StatutEvenement

fake = Faker()


class MaladieFactory(DjangoModelFactory):
    class Meta:
        model = Maladie
        django_get_or_create = ("name",)

    name = factory.Faker("sentence", nb_words=3)


class EspeceFactory(DjangoModelFactory):
    class Meta:
        model = Espece
        django_get_or_create = ("name",)

    name = factory.Faker("sentence", nb_words=3)


class EvenementAnimalFactory(DjangoModelFactory):
    date_creation = factory.Faker("date_this_decade")
    maladie = factory.SubFactory("sa.tests.factories.MaladieFactory")
    espece = factory.SubFactory("sa.tests.factories.EspeceFactory")
    statut_animal = FuzzyChoice([choice[0] for choice in StatutAnimal.choices])
    statut_evenement = FuzzyChoice([choice[0] for choice in StatutEvenement.choices])
    numero_annee = factory.Faker("year")

    adresse_lieu_dit = factory.Faker("street_address")
    commune = factory.Faker("city")
    code_insee = factory.Faker("numerify", text="#####")
    numero_identifiant = factory.Faker("numerify", text="##### #####")
    type_lieu = FuzzyChoice([c[0] for c in StatutAnimal.choices])

    context_suspicion = FuzzyChoice(ContexteSuspicion.values)
    human_involved = FuzzyChoice(HumanInvolved.values)
    description = factory.Faker("paragraph")

    class Meta:
        model = EvenementAnimal

    @factory.lazy_attribute
    def createur(self):
        return Structure.objects.get(libelle="Structure Test")

    @factory.sequence
    def numero_evenement(n):
        return n + 1

    @factory.lazy_attribute
    def date_statut_changed(self):
        return fake.date_this_decade(before_today=True)

    @factory.lazy_attribute
    def date_first_symptoms(self):
        return fake.date_this_decade(before_today=True)

    @factory.lazy_attribute
    def coordinates(self):
        lat, lon = fake.local_latlng(country_code="FR", coords_only=True)
        return Point(float(lon), float(lat))
