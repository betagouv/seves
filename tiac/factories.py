import datetime
import random
from zoneinfo import ZoneInfo

import factory
from django.conf import settings
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from faker import Faker

from core.factories import BaseEtablissementFactory
from core.models import Structure
from ssa.models import CategorieProduit, CategorieDanger
from tiac.constants import (
    EvenementOrigin,
    ModaliteDeclarationEvenement,
    EvenementFollowUp,
    TypeRepas,
    Motif,
    TypeCollectivite,
    DangersSyndromiques,
    EtatPrelevement,
)
from tiac.models import (
    AlimentSuspect,
    TypeAliment,
    MotifAliment,
    EvenementSimple,
    Etablissement,
    Evaluation,
    InvestigationTiac,
    TypeEvenement,
    RepasSuspect,
    AnalyseAlimentaire,
)

fake = Faker()


def random_datetime_utc():
    return fake.date_time_this_decade(tzinfo=ZoneInfo(settings.TIME_ZONE)).replace(second=0, microsecond=0)


def parse_date(value):
    if isinstance(value, str):
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return None


class BaseTiacFactory(DjangoModelFactory):
    class Meta:
        abstract = True

    date_creation = factory.Faker("date_this_decade")
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

    @factory.lazy_attribute
    def date_reception(self):
        return parse_date(fake.date_this_decade())

    @factory.sequence
    def numero_evenement(n):
        return n + 1

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if "date_reception" in kwargs:
            kwargs["date_reception"] = parse_date(kwargs["date_reception"])
        return super()._create(model_class, *args, **kwargs)


class EvenementSimpleFactory(BaseTiacFactory, DjangoModelFactory):
    class Meta:
        model = EvenementSimple

    nb_sick_persons = factory.Faker("pyint", min_value=0, max_value=10)
    follow_up = FuzzyChoice(EvenementFollowUp.values)

    @factory.post_generation
    def with_etablissements(self, create, extracted, **kwargs):  # noqa: F811
        if not create or not extracted:
            return
        EtablissementFactory.create_batch(int(extracted), evenement_simple=self)


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

    agents_confirmes_ars = factory.LazyFunction(
        lambda: random.sample([choice[0] for choice in CategorieDanger.choices], k=random.randint(1, 3))
    )
    danger_syndromiques_suspectes = factory.LazyFunction(
        lambda: random.sample([choice[0] for choice in DangersSyndromiques.choices], k=random.randint(1, 3))
    )


class RepasSuspectFactory(DjangoModelFactory):
    class Meta:
        model = RepasSuspect

    investigation = factory.SubFactory("tiac.factories.InvestigationTiacFactory")
    denomination = factory.Faker("sentence", nb_words=5)
    menu = factory.Faker("paragraph")
    motif_suspicion = factory.LazyFunction(
        lambda: random.sample([choice[0] for choice in Motif.choices], k=random.randint(1, 3))
    )
    datetime_repas = factory.LazyFunction(random_datetime_utc)
    nombre_participant = factory.Faker("pyint", min_value=0, max_value=10)
    departement = factory.SubFactory("core.factories.DepartementFactory")

    type_repas = FuzzyChoice([choice[0] for choice in TypeRepas.choices])

    @factory.post_generation
    def type_collectivite(self, create, extracted, **kwargs):
        if extracted:
            self.type_collectivite = extracted
        elif self.type_repas == TypeRepas.RESTAURATION_COLLECTIVE:
            self.type_collectivite = random.choice([c[0] for c in TypeCollectivite.choices])


class AlimentSuspectFactory(DjangoModelFactory):
    class Meta:
        model = AlimentSuspect

    investigation = factory.SubFactory("tiac.factories.InvestigationTiacFactory")
    denomination = factory.Faker("sentence", nb_words=5)
    type_aliment = FuzzyChoice([choice[0] for choice in TypeAliment.choices])

    description_composition = factory.Faker("paragraph")
    categorie_produit = FuzzyChoice(CategorieProduit.values)
    description_produit = factory.Faker("paragraph")
    motif_suspicion = factory.LazyFunction(
        lambda: random.sample([choice[0] for choice in MotifAliment.choices], k=random.randint(1, 3))
    )

    class Params:
        cuisine = factory.Trait(
            type_aliment=TypeAliment.CUISINE,
            description_composition=factory.Faker("paragraph"),
            categorie_produit="",
            description_produit="",
        )
        simple = factory.Trait(
            type_aliment=TypeAliment.SIMPLE,
            description_composition="",
            categorie_produit=FuzzyChoice(CategorieProduit.values),
            description_produit=factory.Faker("paragraph"),
        )


class AnalyseAlimentaireFactory(DjangoModelFactory):
    class Meta:
        model = AnalyseAlimentaire

    investigation = factory.SubFactory("tiac.factories.InvestigationTiacFactory")

    reference_prelevement = factory.Faker("numerify", text="####-###")
    etat_prelevement = FuzzyChoice(EtatPrelevement.values)
    categorie_danger = factory.LazyFunction(
        lambda: random.sample([choice[0] for choice in CategorieDanger.choices], k=random.randint(1, 3))
    )
    comments = factory.Faker("paragraph")
    sent_to_lnr_cnr = factory.Faker("boolean")
    reference_souche = factory.Faker("sentence", nb_words=1)
