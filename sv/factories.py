import random
import string

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
    Departement,
    OrganismeNuisible,
    FicheZoneDelimitee,
    StatutReglementaire,
    StructurePreleveuse,
    ZoneInfestee,
    Evenement,
    MatricePrelevee,
    EspeceEchantillon,
    Laboratoire,
)
from datetime import datetime


class NumeroFicheFactory(DjangoModelFactory):
    class Meta:
        model = NumeroFiche

    annee = factory.Faker("year")
    numero = factory.Faker("pyint", min_value=0, max_value=1000)


class OrganismeNuisibleFactory(DjangoModelFactory):
    class Meta:
        model = OrganismeNuisible

    code_oepp = factory.Faker("lexify", text="??????")
    libelle_court = factory.Faker("lexify", text="??????")
    libelle_long = factory.Faker("sentence", nb_words=5)


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

    nom = factory.LazyAttribute(lambda _: random.choice(STRUCTURES_PRELEVEUSES))

    class Params:
        not_exploitant = factory.Trait(
            nom=factory.LazyAttribute(
                lambda _: random.choice([s for s in STRUCTURES_PRELEVEUSES if s != STRUCTURE_EXPLOITANT])
            )
        )


class MatricePreleveeFactory(DjangoModelFactory):
    class Meta:
        model = MatricePrelevee
        django_get_or_create = ("libelle",)

    libelle = factory.Sequence(lambda n: f"Matrice {n}")


class EspeceEchantillonFactory(DjangoModelFactory):
    class Meta:
        model = EspeceEchantillon
        django_get_or_create = ("code_oepp", "libelle")

    code_oepp = factory.Sequence(lambda n: f"OEPP{n:04d}")
    libelle = factory.Sequence(lambda n: f"Espèce échantillon {n}")


class LaboratoireFactory(DjangoModelFactory):
    class Meta:
        model = Laboratoire
        django_get_or_create = ("nom",)

    is_active = True
    nom = factory.Sequence(lambda n: f"Laboratoire {n}")
    confirmation_officielle = False


class PrelevementFactory(DjangoModelFactory):
    class Meta:
        model = Prelevement

    lieu = factory.SubFactory("sv.factories.LieuFactory")
    numero_echantillon = factory.Faker("numerify", text="#####")
    date_prelevement = factory.Faker("date_this_decade")
    matrice_prelevee = factory.SubFactory("sv.factories.MatricePreleveeFactory")
    espece_echantillon = factory.SubFactory("sv.factories.EspeceEchantillonFactory")
    is_officiel = factory.Faker("boolean")
    resultat = FuzzyChoice([choice[0] for choice in Prelevement.Resultat.choices])
    type_analyse = Prelevement.TypeAnalyse.PREMIERE_INTENTION

    @factory.lazy_attribute
    def structure_preleveuse(self):
        if self.is_officiel:
            return StructurePreleveuseFactory(not_exploitant=True)
        return StructurePreleveuseFactory()

    @factory.lazy_attribute
    def laboratoire(self):
        if self.type_analyse == Prelevement.TypeAnalyse.CONFIRMATION:
            return LaboratoireFactory(confirmation_officielle=True)
        return LaboratoireFactory()

    @factory.lazy_attribute
    def numero_rapport_inspection(self):
        if self.is_officiel:
            return "".join(random.choices(string.digits, k=5))
        return ""


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

    commentaire = factory.Faker("paragraph")
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
    visibilite = Visibilite.LOCALE
    etat = Evenement.Etat.EN_COURS

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
