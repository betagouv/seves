from datetime import datetime

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from core.models import Structure
from tiac.constants import EvenementOrigin, ModaliteDeclarationEvenement, EvenementFollowUp
from tiac.models import EvenementSimple


class EvenementSimpleFactory(DjangoModelFactory):
    class Meta:
        model = EvenementSimple

    date_creation = factory.Faker("date_this_decade")
    date_reception = factory.Faker("date_this_decade")
    numero_annee = factory.Faker("year")

    evenement_origin = FuzzyChoice(EvenementOrigin.values)
    modalites_declaration = FuzzyChoice(ModaliteDeclarationEvenement.values)

    contenu = factory.Faker("paragraph")
    notify_ars = factory.Faker("boolean")
    nb_sick_persons = factory.Faker("pyint", min_value=0, max_value=10)

    follow_up = FuzzyChoice(EvenementFollowUp.values)

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

    @factory.sequence
    def numero_evenement(n):
        return n + 1
