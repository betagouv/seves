import random
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from core.models import Visibilite, Structure
from .constants import STATUTS_REGLEMENTAIRES, STRUCTURES_PRELEVEUSES, STRUCTURE_EXPLOITANT
from .models import (
    Prelevement,
    Lieu,
    NumeroFiche,
    FicheDetection,
    Etat,
    Departement,
    OrganismeNuisible,
    FicheZoneDelimitee,
    StatutReglementaire,
    StructurePreleveuse,
    ZoneInfestee,
    Evenement,
)
from datetime import datetime


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


class StatutReglementaireFactory(DjangoModelFactory):
    class Meta:
        model = StatutReglementaire
        django_get_or_create = ("libelle",)

    code = factory.LazyAttribute(lambda _: random.choice(list(STATUTS_REGLEMENTAIRES.keys())))
    libelle = factory.LazyAttribute(lambda obj: STATUTS_REGLEMENTAIRES[obj.code])


class StructurePreleveuseFactory(DjangoModelFactory):
    class Meta:
        model = StructurePreleveuse
        django_get_or_create = ("nom",)

    nom = factory.LazyAttribute(
        lambda _: random.choice([s for s in STRUCTURES_PRELEVEUSES if s != STRUCTURE_EXPLOITANT])
    )


class PrelevementFactory(DjangoModelFactory):
    class Meta:
        model = Prelevement

    type_analyse = FuzzyChoice([choice[0] for choice in Prelevement.TypeAnalyse.choices])
    lieu = factory.SubFactory("sv.factories.LieuFactory")
    structure_preleveuse = factory.SubFactory("sv.factories.StructurePreleveuseFactory")
    numero_echantillon = factory.Faker("numerify", text="#####")
    date_prelevement = factory.Faker("date_this_decade")
    is_officiel = factory.Faker("boolean")
    resultat = FuzzyChoice([choice[0] for choice in Prelevement.Resultat.choices])
    numero_rapport_inspection = factory.Faker("numerify", text="#####")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if kwargs["is_officiel"] is False:
            kwargs["numero_rapport_inspection"] = ""
        return super()._create(model_class, *args, **kwargs)


class LieuFactory(DjangoModelFactory):
    class Meta:
        model = Lieu

    nom = factory.Faker("sentence", nb_words=2)
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
    date_premier_signalement = factory.Faker("date_this_decade")
    commentaire = factory.Faker("paragraph")
    mesures_conservatoires_immediates = factory.Faker("paragraph")
    mesures_consignation = factory.Faker("paragraph")
    mesures_phytosanitaires = factory.Faker("paragraph")
    mesures_surveillance_specifique = factory.Faker("paragraph")
    date_creation = factory.Faker("date_this_decade")
    vegetaux_infestes = factory.Faker("sentence")
    numero = factory.SubFactory("sv.factories.NumeroFicheFactory")
    evenement = factory.SubFactory("sv.factories.EvenementFactory")

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


class FicheZoneFactory(DjangoModelFactory):
    date_creation = factory.Faker("date_this_decade")
    numero = factory.SubFactory("sv.factories.NumeroFicheFactory")

    rayon_zone_tampon = factory.fuzzy.FuzzyFloat(1, 100, precision=2)
    unite_rayon_zone_tampon = factory.fuzzy.FuzzyChoice(FicheZoneDelimitee.UnitesRayon)
    surface_tampon_totale = factory.fuzzy.FuzzyFloat(1, 100, precision=2)
    unite_surface_tampon_totale = factory.fuzzy.FuzzyChoice(FicheZoneDelimitee.UnitesSurfaceTamponTolale)

    class Meta:
        model = FicheZoneDelimitee

    @factory.lazy_attribute
    def createur(self):
        return Structure.objects.get(libelle="Structure Test")

    @classmethod
    def from_detection(cls, detection: FicheDetection, **kwargs):
        return cls(evenement=detection.evenement, **kwargs)


class ZoneInfesteeFactory(DjangoModelFactory):
    class Meta:
        model = ZoneInfestee

    nom = factory.Sequence(lambda n: "Ma zone infestée {}".format(n))
    fiche_zone_delimitee = factory.SubFactory("sv.factories.FicheZoneFactory")

    surface_infestee_totale = factory.fuzzy.FuzzyFloat(1, 100, precision=2)
    unite_surface_infestee_totale = factory.fuzzy.FuzzyChoice(ZoneInfestee.UnitesSurfaceInfesteeTotale)
    rayon = factory.fuzzy.FuzzyFloat(1, 100, precision=2)
    unite_rayon = factory.fuzzy.FuzzyChoice(ZoneInfestee.UnitesRayon)
    caracteristique_principale = factory.fuzzy.FuzzyChoice(ZoneInfestee.CaracteristiquePrincipale)


class EvenementFactory(DjangoModelFactory):
    class Meta:
        model = Evenement

    date_creation = factory.Faker("date_this_decade")
    numero = factory.SubFactory("sv.factories.NumeroFicheFactory")
    organisme_nuisible = factory.SubFactory("sv.factories.OrganismeNuisibleFactory")
    statut_reglementaire = factory.SubFactory("sv.factories.StatutReglementaireFactory")
    visibilite = Visibilite.LOCAL

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if kwargs["visibilite"] == Visibilite.BROUILLON:
            kwargs["numero"] = None
        return super()._create(model_class, *args, **kwargs)

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
