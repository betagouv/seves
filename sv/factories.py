import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from core.models import Visibilite, Structure
from .models import Prelevement, Lieu, NumeroFiche, FicheDetection, Etat, Departement, OrganismeNuisible


class NumeroFicheFactory(DjangoModelFactory):
    class Meta:
        model = NumeroFiche

    annee = factory.Faker("year")
    numero = factory.Faker("pyint", min_value=0, max_value=1000)


class EtatFactory(DjangoModelFactory):
    class Meta:
        model = Etat

    libelle = factory.Faker("word")


class OrganismeNuisibleFactory(DjangoModelFactory):
    class Meta:
        model = OrganismeNuisible

    code_oepp = factory.Faker("lexify", text="??????")
    libelle_court = factory.Faker("lexify", text="??????")


class DepartementFactory(DjangoModelFactory):
    class Meta:
        model = Departement
        django_get_or_create = ("nom",)

    @factory.lazy_attribute
    def _departement(self):
        return FuzzyChoice(Departement.objects.all()).fuzz()

    nom = factory.LazyAttribute(lambda o: o._departement.nom)
    numero = factory.LazyAttribute(lambda o: o._departement.numero)
    region = factory.LazyAttribute(lambda o: o._departement.region)


class PrelevementFactory(DjangoModelFactory):
    class Meta:
        model = Prelevement

    lieu = factory.SubFactory("sv.factories.LieuFactory")
    numero_echantillon = factory.Faker("numerify", text="#####")
    date_prelevement = factory.Faker("date_this_decade")
    is_officiel = factory.Faker("boolean")
    resultat = FuzzyChoice([choice[0] for choice in Prelevement.Resultat.choices])
    numero_resytal = factory.Faker("numerify", text="#####")


class LieuFactory(DjangoModelFactory):
    class Meta:
        model = Lieu

    fiche_detection = factory.SubFactory("sv.factories.FicheDetectionFactory")
    wgs84_longitude = factory.Faker("longitude")
    wgs84_latitude = factory.Faker("latitude")
    adresse_lieu_dit = factory.Faker("street_address")
    commune = factory.Faker("city")
    code_insee = factory.Faker("numerify", text="#####")
    departement = factory.SubFactory("sv.factories.DepartementFactory")
    is_etablissement = factory.Faker("boolean")
    nom_etablissement = factory.Faker("company")
    activite_etablissement = factory.Faker("job")
    pays_etablissement = factory.Faker("country")
    raison_sociale_etablissement = factory.Faker("company_suffix")
    adresse_etablissement = factory.Faker("address")
    siret_etablissement = factory.Faker("numerify", text="##############")
    code_inupp_etablissement = factory.Faker("numerify", text="#######")


class FicheDetectionFactory(DjangoModelFactory):
    class Meta:
        model = FicheDetection

    numero_europhyt = factory.Faker("bothify", text="#?#?#?#?")
    numero_rasff = factory.Faker("bothify", text="#?#?#?#?#")
    organisme_nuisible = factory.SubFactory("sv.factories.OrganismeNuisibleFactory")
    date_premier_signalement = factory.Faker("date_this_decade")
    commentaire = factory.Faker("paragraph")
    mesures_conservatoires_immediates = factory.Faker("paragraph")
    mesures_consignation = factory.Faker("paragraph")
    mesures_phytosanitaires = factory.Faker("paragraph")
    mesures_surveillance_specifique = factory.Faker("paragraph")
    date_creation = factory.Faker("date_this_decade")
    vegetaux_infestes = factory.Faker("sentence")
    numero = factory.SubFactory("sv.factories.NumeroFicheFactory")
    visibilite = Visibilite.LOCAL

    @factory.lazy_attribute
    def createur(self):
        return Structure.objects.get(libelle="Structure Test")

    @factory.post_generation
    def etat(self, create, extracted, **kwargs):
        if "libelle" in kwargs:
            self.etat = Etat.objects.create(**kwargs) if create else Etat(**kwargs)
        else:
            self.etat = Etat.objects.get(id=Etat.get_etat_initial())

    @factory.post_generation
    def date_creation(self, create, extracted, **kwargs):  # noqa: F811
        if extracted and create:
            self.date_creation = extracted
            self.save()
