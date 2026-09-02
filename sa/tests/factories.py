from datetime import timedelta

from django.contrib.gis.geos import Point
from django_countries import Countries
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from faker import Faker

from core.models import Structure
from sa.models import Analyse, Espece, EvenementAnimal, Laboratoire, Maladie, MethodeAnalyse
from sa.models.analyse import ResultatAnalyse
from sa.models.evenement import ContexteSuspicion, HumanInvolved, StatutAnimal, StatutEvenement, TypeLieu
from sa.models.laboratoire import LaboratoireType
from sa.models.maladie import DescriptionType

fake = Faker()


REALISTIC_MALADIES = [
    ("Salmonellose (Salmonella)", "SAL", DescriptionType.SALMONELLE, True, False, True),
    ("Rage", "RAG", DescriptionType.NOTIFY_ASAP, True, False, True),
    ("Brucellose", "BRU", DescriptionType.NOTIFY_ASAP, True, False, True),
    ("Tuberculose", "TUB", DescriptionType.TUBERCULOSE, True, False, True),
    ("Fièvre catarrhale ovine", "FCO", DescriptionType.NOTIFY_CONFIRMED, False, False, True),
    ("Acarapiose des abeilles (Acarapis woodi)", "DIV", DescriptionType.NOTIFY_CONFIRMED, False, False, True),
    ("Adénomatose pulmonaire ovine", "DIV", DescriptionType.NOTIFY_CONFIRMED, False, False, True),
]


class MaladieFactory(DjangoModelFactory):
    class Meta:
        model = Maladie
        django_get_or_create = ("name",)

    class Params:
        maladie_ref = factory.Iterator(REALISTIC_MALADIES)

    name = factory.LazyAttribute(lambda o: o.maladie_ref[0])
    acronym = factory.LazyAttribute(lambda o: o.maladie_ref[1])
    description_type = factory.LazyAttribute(lambda o: o.maladie_ref[2])
    needs_arrete = factory.LazyAttribute(lambda o: o.maladie_ref[3])
    needs_dates_desinfection = factory.LazyAttribute(lambda o: o.maladie_ref[4])
    needs_date_nd = factory.LazyAttribute(lambda o: o.maladie_ref[5])


class TuberculoseFactory(MaladieFactory):
    class Params:
        maladie_ref = REALISTIC_MALADIES[3]


class AcarapioseFactory(MaladieFactory):
    class Params:
        maladie_ref = REALISTIC_MALADIES[5]


class AdenomatoseFactory(MaladieFactory):
    class Params:
        maladie_ref = REALISTIC_MALADIES[6]


class EspeceFactory(DjangoModelFactory):
    class Meta:
        model = Espece
        django_get_or_create = ("name",)

    name = factory.Faker("sentence", nb_words=3)


class LaboratoireFactory(DjangoModelFactory):
    class Meta:
        model = Laboratoire
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Laboratoire {n}")
    external_id = factory.Sequence(lambda n: f"LAB-{n:06d}")
    code = factory.Sequence(lambda n: f"CODE-{n}")
    laboratoire_type = FuzzyChoice(LaboratoireType.values)


class MethodeAnalyseFactory(DjangoModelFactory):
    class Meta:
        model = MethodeAnalyse
        django_get_or_create = ("libelle",)
        skip_postgeneration_save = True

    libelle = factory.Sequence(lambda n: f"Méthode {n}")

    @factory.post_generation
    def laboratoires(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.laboratoires.set(extracted)


class EvenementAnimalFactory(DjangoModelFactory):
    date_creation = factory.Faker("date_this_decade")
    maladie = factory.SubFactory("sa.tests.factories.MaladieFactory")
    espece = factory.SubFactory("sa.tests.factories.EspeceFactory")
    statut_animal = FuzzyChoice([choice[0] for choice in StatutAnimal.choices])
    statut_evenement = FuzzyChoice([choice[0] for choice in StatutEvenement.choices])
    numero_annee = factory.Faker("year")

    numero_identifiant_etablissement = factory.Sequence(lambda n: f"ID-{n:06d}")
    raison_sociale_etablissement = factory.Faker("company", locale="fr_FR")
    departement_etablissement = factory.SubFactory("core.factories.DepartementFactory")
    autre_identifiant_etablissement = factory.Sequence(lambda n: f"TEST-{n:06d}")
    adresse_lieu_dit_etablissement = factory.Faker("street_address", locale="fr_FR")
    code_insee_etablissement = factory.LazyFunction(lambda: fake.numerify("#####"))
    siret_etablissement = factory.LazyFunction(lambda: fake.numerify("##############"))
    commune_etablissement = factory.Faker("city", locale="fr_FR")
    pays_etablissement = FuzzyChoice([c.code for c in Countries()])

    adresse_lieu_dit = factory.Faker("street_address")
    commune = factory.Faker("city")
    code_insee = factory.Faker("numerify", text="#####")
    numero_identifiant = factory.Faker("numerify", text="##### #####")

    context_suspicion = FuzzyChoice(ContexteSuspicion.values)
    human_involved = FuzzyChoice(HumanInvolved.values)
    description = factory.Faker("paragraph")

    class Meta:
        model = EvenementAnimal

    class Params:
        particulier = factory.Trait(
            numero_identifiant_etablissement="",
            raison_sociale_etablissement="",
            departement_etablissement=None,
            autre_identifiant_etablissement="",
            adresse_lieu_dit_etablissement="",
            code_insee_etablissement="",
            siret_etablissement="",
            commune_etablissement="",
            pays_etablissement="",
            nom_particulier=factory.Faker("last_name", locale="fr_FR"),
            prenom_particulier=factory.Faker("first_name", locale="fr_FR"),
            adresse_particulier=factory.Faker("street_address", locale="fr_FR"),
            commune_particulier=factory.Faker("city", locale="fr_FR"),
            departement_particulier=factory.SubFactory("core.factories.DepartementFactory"),
            code_insee_particulier=factory.LazyFunction(lambda: fake.numerify("#####")),
            email_particulier=factory.Faker("email"),
            telephone_particulier=factory.Faker("phone_number", locale="fr_FR"),
        )

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

    @factory.lazy_attribute
    def date_apms(self):
        if self.maladie.needs_arrete:
            return fake.date_this_decade()

    @factory.lazy_attribute
    def date_apdi(self):
        if self.maladie.needs_arrete:
            return fake.date_this_decade()

    @factory.lazy_attribute
    def date_levee(self):
        if self.maladie.needs_arrete:
            return fake.date_this_decade()

    @factory.lazy_attribute
    def type_lieu(self):
        return FuzzyChoice([value for value, _ in TypeLieu.choices_for_statut_animal(self.statut_animal)]).fuzz()

    @factory.lazy_attribute
    def date_d_zero(self):
        if self.maladie.needs_dates_desinfection:
            return fake.date_this_decade()

    @factory.lazy_attribute
    def date_nd1(self):
        if self.maladie.needs_dates_desinfection:
            return fake.date_between(start_date=self.date_d_zero, end_date=self.date_d_zero + timedelta(days=30))

    @factory.lazy_attribute
    def date_nd2(self):
        if self.maladie.needs_dates_desinfection:
            return fake.date_between(start_date=self.date_nd1, end_date=self.date_nd1 + timedelta(days=30))


class AnalyseFactory(DjangoModelFactory):
    class Meta:
        model = Analyse
        skip_postgeneration_save = True

    evenement = factory.SubFactory(EvenementAnimalFactory)
    maladie = factory.SelfAttribute("evenement.maladie")
    date_prelevement = factory.LazyFunction(lambda: fake.date_this_decade(before_today=True))
    laboratoire = factory.SubFactory(LaboratoireFactory)
    methode = factory.SubFactory(MethodeAnalyseFactory)
    resultat = FuzzyChoice(ResultatAnalyse.values)
    resultat_confirmation = FuzzyChoice([True, False])

    @factory.post_generation
    def link_methode_to_laboratoire(self, create, extracted, **kwargs):
        if create:
            self.methode.laboratoires.add(self.laboratoire)
