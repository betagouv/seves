import random
import string
from datetime import datetime

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from faker import Faker

from core.models import Visibilite, Structure
from .constants import (
    STATUTS_REGLEMENTAIRES,
    STRUCTURES_PRELEVEUSES,
    STRUCTURE_EXPLOITANT,
    STATUTS_EVENEMENT,
    CONTEXTES,
    SITES_INSPECTION,
    DEPARTEMENTS,
    REGIONS,
    POSITION_CHAINE_DISTRIBUTION,
)
from .models import (
    Prelevement,
    Lieu,
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
    StatutEvenement,
    Contexte,
    SiteInspection,
    Region,
    PositionChaineDistribution,
)

fake = Faker()


class OrganismeNuisibleFactory(DjangoModelFactory):
    class Meta:
        model = OrganismeNuisible
        django_get_or_create = ("libelle_court",)

    code_oepp = factory.Faker("lexify", text="??????")
    libelle_court = factory.Faker("lexify", text="??????")
    libelle_long = factory.Faker("sentence", nb_words=5)


class RegionFactory(DjangoModelFactory):
    class Meta:
        model = Region
        django_get_or_create = ("nom",)

    nom = factory.fuzzy.FuzzyChoice(REGIONS)


class DepartementFactory(DjangoModelFactory):
    class Meta:
        model = Departement
        django_get_or_create = ("nom",)

    region = factory.SubFactory("sv.factories.RegionFactory")

    @factory.lazy_attribute
    def numero(self):
        return random.choice([d[0] for d in DEPARTEMENTS if self.region.nom == d[2]])

    @factory.lazy_attribute
    def nom(self):
        return [d[1] for d in DEPARTEMENTS if self.numero == d[0]][0]


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


class StatutEvenementFactory(DjangoModelFactory):
    class Meta:
        model = StatutEvenement
        django_get_or_create = ("libelle",)

    libelle = factory.lazy_attribute(lambda _: random.choice(STATUTS_EVENEMENT))


class ContexteFactory(DjangoModelFactory):
    class Meta:
        model = Contexte
        django_get_or_create = ("nom",)

    nom = factory.lazy_attribute(lambda _: random.choice(CONTEXTES))


class SiteInspectionFactory(DjangoModelFactory):
    class Meta:
        model = SiteInspection
        django_get_or_create = ("nom",)

    nom = factory.lazy_attribute(lambda _: random.choice(random.choices(SITES_INSPECTION)))


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
    date_rapport_analyse = factory.Faker("date_this_decade")

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
            return "".join(random.choices(string.digits, k=2)) + "-" + "".join(random.choices(string.digits, k=6))
        return ""

    @classmethod
    def build_with_some_related_objects_saved(cls, *args, **kwargs):
        matrice_prelevee = MatricePreleveeFactory()
        espece = EspeceEchantillonFactory()
        return cls.build(matrice_prelevee=matrice_prelevee, espece_echantillon=espece, *args, **kwargs)

    @classmethod
    def create_minimal(cls, **kwargs):
        return cls.create(
            numero_echantillon="",
            date_prelevement=None,
            matrice_prelevee=None,
            espece_echantillon=None,
            laboratoire=None,
            numero_rapport_inspection="",
            date_rapport_analyse=None,
            **kwargs,
        )


class PositionChaineDistributionFactory(DjangoModelFactory):
    class Meta:
        model = PositionChaineDistribution
        django_get_or_create = ("libelle",)

    libelle = factory.lazy_attribute(lambda _: random.choice(POSITION_CHAINE_DISTRIBUTION))


class LieuFactory(DjangoModelFactory):
    class Meta:
        model = Lieu

    nom = factory.Faker("sentence", nb_words=2)
    fiche_detection = factory.SubFactory("sv.factories.FicheDetectionFactory")

    wgs84_longitude = factory.LazyFunction(lambda: float(fake.longitude()))
    wgs84_latitude = factory.LazyFunction(lambda: float(fake.latitude()))
    adresse_lieu_dit = factory.Faker("street_address")
    commune = factory.Faker("city")
    code_insee = factory.Faker("numerify", text="#####")
    departement = factory.SubFactory("sv.factories.DepartementFactory")
    is_etablissement = factory.Faker("boolean")
    activite_etablissement = factory.Faker("job")
    pays_etablissement = factory.Faker("country")
    raison_sociale_etablissement = factory.Faker("company_suffix")
    adresse_etablissement = factory.Faker("address")
    siret_etablissement = factory.Faker("numerify", text="##############")
    code_inupp_etablissement = factory.Faker("numerify", text="#######")
    site_inspection = factory.SubFactory("sv.factories.SiteInspectionFactory")
    position_chaine_distribution_etablissement = factory.SubFactory("sv.factories.PositionChaineDistributionFactory")

    @classmethod
    def create_minimal(cls, **kwargs):
        return cls.create(
            wgs84_longitude=None,
            wgs84_latitude=None,
            adresse_lieu_dit="",
            commune="",
            code_insee="",
            departement=None,
            is_etablissement=False,
            activite_etablissement="",
            pays_etablissement="",
            raison_sociale_etablissement="",
            adresse_etablissement="",
            siret_etablissement="",
            code_inupp_etablissement="",
            site_inspection=None,
            position_chaine_distribution_etablissement=None,
            **kwargs,
        )


class FicheDetectionFactory(DjangoModelFactory):
    class Meta:
        model = FicheDetection

    date_premier_signalement = factory.Faker("date_this_decade")
    commentaire = factory.Faker("paragraph")
    mesures_conservatoires_immediates = factory.Faker("paragraph")
    mesures_consignation = factory.Faker("paragraph")
    mesures_phytosanitaires = factory.Faker("paragraph")
    mesures_surveillance_specifique = factory.Faker("paragraph")
    date_creation = factory.Faker("date_this_decade")
    vegetaux_infestes = factory.Faker("sentence")
    evenement = factory.SubFactory("sv.factories.EvenementFactory")
    statut_evenement = factory.SubFactory("sv.factories.StatutEvenementFactory")
    contexte = factory.SubFactory("sv.factories.ContexteFactory")

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

    @factory.post_generation
    def with_lieu(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        LieuFactory(fiche_detection=self)

    @factory.post_generation
    def with_prelevement(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        lieu = LieuFactory(fiche_detection=self)
        PrelevementFactory(lieu=lieu)


class FicheZoneFactory(DjangoModelFactory):
    date_creation = factory.Faker("date_this_decade")

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
    organisme_nuisible = factory.SubFactory("sv.factories.OrganismeNuisibleFactory")
    statut_reglementaire = factory.SubFactory("sv.factories.StatutReglementaireFactory")
    visibilite = Visibilite.LOCALE
    etat = Evenement.Etat.EN_COURS
    numero_annee = factory.Faker("year")
    numero_evenement = factory.Faker("pyint", min_value=0, max_value=1000)
    numero_europhyt = factory.Faker("bothify", text="#?#?#?#?")
    numero_rasff = factory.Faker("bothify", text="#?#?#?#?#")

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
