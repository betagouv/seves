import random
import datetime

import factory
from zoneinfo import ZoneInfo
from django.conf import settings
from django.utils import timezone
from faker import Faker
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice

from core.factories import BaseEtablissementFactory
from core.models import Structure
from tiac.constants import EvenementOrigin, ModaliteDeclarationEvenement, EvenementFollowUp
from tiac.models import EvenementSimple, Etablissement, Evaluation, InvestigationTiac, TypeEvenement

fake = Faker()


def random_datetime_utc():
    return fake.date_time_this_decade(tzinfo=ZoneInfo(settings.TIME_ZONE)).replace(second=0, microsecond=0)


class BaseTiacFactory(DjangoModelFactory):
    class Meta:
        abstract = True

    date_creation = factory.Faker("date_this_decade")
    date_reception = factory.Faker("date_this_decade")
    numero_annee = factory.Faker("year")

    evenement_origin = FuzzyChoice(EvenementOrigin.values)
    modalites_declaration = FuzzyChoice(ModaliteDeclarationEvenement.values)
    contenu = factory.Faker("paragraph")
    notify_ars = factory.Faker("boolean")

    @factory.lazy_attribute
    def createur(self):
        return Structure.objects.get(libelle="Structure Test")

    @factory.post_generation
    def date_creation(self, create, extracted, **kwargs):  # noqa: F811
        if extracted and create:
            if isinstance(extracted, str):
                self.date_creation = timezone.make_aware(datetime.datetime.strptime(extracted, "%Y-%m-%d"))
            else:
                self.date_creation = extracted
            self.save()

    @factory.sequence
    def numero_evenement(n):
        return n + 1


class EvenementSimpleFactory(BaseTiacFactory, DjangoModelFactory):
    class Meta:
        model = EvenementSimple

    nb_sick_persons = factory.Faker("pyint", min_value=0, max_value=10)
    follow_up = FuzzyChoice(EvenementFollowUp.values)


class EtablissementFactory(BaseEtablissementFactory, DjangoModelFactory):
    class Meta:
        model = Etablissement

    evenement_simple = factory.SubFactory("tiac.factories.EvenementSimpleFactory")

    type_etablissement = factory.Faker("sentence", nb_words=2)

    class Params:
        inspection = factory.Trait(
            has_inspection=True,
            numero_resytal=factory.Faker("numerify", text="##############"),
            evaluation=random.choice([c[0] for c in Evaluation.values]),
            commentaire=factory.Faker("paragraph"),
        )


class InvestigationTiacFactory(BaseTiacFactory, DjangoModelFactory):
    class Meta:
        model = InvestigationTiac

    will_trigger_inquiry = factory.Faker("boolean")
    numero_sivss = factory.Faker("numerify", text="######")
    type_evenement = FuzzyChoice([choice[0] for choice in TypeEvenement.choices])

    nb_sick_persons = factory.Faker("pyint", min_value=0, max_value=10)
    nb_sick_persons_to_hospital = factory.Faker("pyint", min_value=0, max_value=10)
    nb_dead_persons = factory.Faker("pyint", min_value=0, max_value=10)
    datetime_first_symptoms = factory.LazyFunction(random_datetime_utc)
    datetime_last_symptoms = factory.LazyFunction(random_datetime_utc)
