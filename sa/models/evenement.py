import datetime
from enum import auto

from django.contrib.gis.db.models import PointField
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils.functional import classproperty
from django_countries.fields import CountryField
import reversion
from reversion.models import Version

from core.mixins import AllowModificationMixin, WithNumeroMixin, normalize
from core.models import Structure
from core.soft_delete_mixins import AllowsSoftDeleteMixin
from sa.managers import EvenementAnimalManager
from sa.models.maladie import Maladie


class Espece(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.name


class StatutAnimal(models.TextChoices):
    SAUVAGE = auto(), "Sauvage"
    DETENU = auto(), "Détenu"


class StatutEvenement(models.TextChoices):
    SUSPECT = auto(), "Suspect"
    CONFIRME = auto(), "Confirmé"
    INFIRME = auto(), "Infirmé"
    NON_RETENU = auto(), "Non retenu"


class Foyer(models.TextChoices):
    PRIMAIRE = "primaire", "Primaire"
    SECONDAIRE = "secondaire", "Secondaire"


class OrigineInfection(models.TextChoices):
    CONTACT_DIRECT = auto(), "Contact direct"
    IMPORTATION = auto(), "Importation"
    INCONNUE = auto(), "Inconnue"
    INTERVENTION_HUMAINE = auto(), "Intervention humaine"
    VECTEUR = auto(), "Vecteur"


class MesureDeControle(models.TextChoices):
    # Values in English to ease the integration with ADIS system
    ANTE_AND_POST_MORTEM_INSPECTIONS = (
        "Ante and post-mortem inspections",
        "Inspections ante mortem et post mortem",
    )
    COMPARTMENTALISATION = "Compartmentalisation", "Compartimentation"
    CONTROL_OF_VECTORS = "Control of vectors", "Contrôle des vecteurs"
    CONTROL_OF_WILDLIFE_RESERVOIRS = (
        "Control of wildlife reservoirs",
        "Contrôle des réservoirs de la faune sauvage",
    )
    DECONTAMINATION_OF_PREMISES_DISINFECTION = (
        "Decontamination of premises / Disinfection",
        "Décontamination des locaux / désinfection",
    )
    DIPPING_SPRAYING_FOR_CONTROL_OF_VECTORS_OR_PARASITES = (
        "Dipping / Spraying for control of vectors or parasites",
        "Bains / pulvérisations pour lutter contre les vecteurs ou les parasites",
    )
    DISEASE_NOTIFICATION = "Disease notification", "Notification d’une maladie"
    DISINFECTION = "Disinfection", "Désinfection"
    DISINFECTION_DISINFESTATION = (
        "Disinfection / Disinfestation",
        "Désinfection / désinfestation",
    )
    DISINFESTATION = "Disinfestation", "Désinfestation"
    EMERGENCY_HARVEST = "Emergency harvest", "Récolte d’urgence"
    GENERAL_SURVEILLANCE = "General Surveillance", "Surveillance générale"
    KILLING_FOR_COMMERCIAL_USE_OR_OWN_USE = (
        "Killing for commercial use or own use",
        "Abattage à des fins commerciales ou pour usage personnel",
    )
    MONITORING = "Monitoring", "Suivi"
    MOVEMENT_CONTROL = "Movement control", "Contrôle des mouvements"
    OFFICIAL_DESTRUCTION_OF_ANIMAL_PRODUCTS = (
        "Official destruction of animal products",
        "Destruction officielle des produits animaux",
    )
    OFFICIAL_DISPOSAL_OF_CARCASSES_BY_PRODUCTS_AND_WASTE = (
        "Official disposal of carcasses, by-products and waste",
        "Élimination officielle des carcasses, sous-produits animaux et déchets",
    )
    OFFICIAL_VACCINATION = "Official vaccination", "Vaccination officielle"
    PRECAUTIONS_AT_THE_BORDERS = (
        "Precautions at the borders",
        "Mesures de précaution aux frontières",
    )
    PROCESS_TO_INACTIVATE_THE_PATHOGENIC_AGENT = (
        "Process to inactivate the pathogenic agent in products or by-products",
        "Procédé d’inactivation de l’agent pathogène dans les produits ou sous-produits animaux",
    )
    QUARANTINE = "Quarantine", "Quarantaine"
    SCREENING = "Screening", "Dépistage"
    SELECTIVE_KILLING_AND_DISPOSAL = (
        "Selective killing and disposal",
        "Abattage sélectif et élimination",
    )
    SLAUGHTER = (
        "Slaughter",
        "Abattage ciblé d’animaux infectés ou suspects",
    )
    STAMPING_OUT = (
        "Stamping out",
        "Abattage sanitaire total du foyer",
    )
    SURVEILLANCE_OUTSIDE_THE_RESTRICTED_ZONE = (
        "Surveillance outside the restricted zone",
        "Surveillance hors de la zone de restriction",
    )
    SURVEILLANCE_WITHIN_THE_RESTRICTED_ZONE = (
        "Surveillance within the restricted zone",
        "Surveillance à l’intérieur de la zone de restriction",
    )
    TARGETED_SURVEILLANCE = "Targeted Surveillance", "Surveillance ciblée"
    TRACEABILITY = "Traceability", "Traçabilité"
    TREATMENT = "Treatment", "Traitement"
    VACCINATION = "Vaccination", "Vaccination"
    VACCINATION_IN_RESPONSE_TO_THE_OUTBREAKS = (
        "Vaccination in response to the outbreak(s)",
        "Vaccination en réponse à un ou plusieurs foyers",
    )
    VACCINATION_PROHIBITED = "Vaccination prohibited", "Vaccination interdite"
    VECTOR_SURVEILLANCE = "Vector surveillance", "Surveillance des vecteurs"
    ZONING = "Zoning", "Zonage"


class TypeLieu(models.TextChoices):
    APIARY = "Apiary", "Ruche"
    BACKYARD = "Backyard", "Basse-cour"
    CAGE_AQUATIC_ENVIRONMENT = "Cage (aquatic environment)", "Cage (milieu aquatique)"
    COASTAL_AREA_MARINE_AREA = "Coastal area - marine area", "Zone côtière - zone maritime"
    ESTUARY = "Estuary", "Estuaire"
    FARM = (
        "Farm (terrestrial or aquatic, including educational farm, excluding backyard)",
        "Élevage (terrestre ou aquatique, y compris ferme pédagogique, hors basse-cour)",
    )
    FOREST = "Forest (excluding farming)", "Forêt (hors élevage)"
    LAKE = "Lake", "Lac"
    LIVESTOCK_MARKET_FAIR_EXHIBITION_TRANSPORT = (
        "Livestock market - fair - exhibition - transport",
        "Marché aux bestiaux - foire - exposition - transport",
    )
    NATURAL_PARK_NATURE_RESERVE_GAME_PARK = (
        "Natural park - nature reserve - game park",
        "Parc naturel - réserve - parc de chasse",
    )
    NOT_APPLICABLE = "Not applicable", "Non applicable"
    OTHER = "Other", "Autre"
    POND_SMALL_POND = "Pond - small pond", "Étang - mare"
    RESERVOIR_DAM = "Reservoir - dam", "Réservoir - barrage"
    RIVER_SYSTEM_RUNNING_WATERS = "River system - running waters", "Réseau hydrographique - eaux courantes"
    SHELLFISH_BED = "Shellfish bed", "Banc de coquillage"
    SLAUGHTERHOUSE = "Slaughterhouse", "Abattoir"
    ZOO = "Zoo", "Parc zoologique"

    @classproperty
    def choices_detenu(cls):
        members = (
            cls.APIARY,
            cls.BACKYARD,
            cls.CAGE_AQUATIC_ENVIRONMENT,
            cls.COASTAL_AREA_MARINE_AREA,
            cls.ESTUARY,
            cls.FARM,
            cls.LAKE,
            cls.LIVESTOCK_MARKET_FAIR_EXHIBITION_TRANSPORT,
            cls.NATURAL_PARK_NATURE_RESERVE_GAME_PARK,
            cls.NOT_APPLICABLE,
            cls.OTHER,
            cls.POND_SMALL_POND,
            cls.SHELLFISH_BED,
            cls.SLAUGHTERHOUSE,
            cls.ZOO,
        )
        return sorted(((member.value, member.label) for member in members), key=lambda choice: normalize(choice[1]))

    @classproperty
    def choices_sauvage(cls):
        members = (
            cls.COASTAL_AREA_MARINE_AREA,
            cls.ESTUARY,
            cls.FOREST,
            cls.LAKE,
            cls.NATURAL_PARK_NATURE_RESERVE_GAME_PARK,
            cls.NOT_APPLICABLE,
            cls.OTHER,
            cls.POND_SMALL_POND,
            cls.RESERVOIR_DAM,
            cls.RIVER_SYSTEM_RUNNING_WATERS,
            cls.SHELLFISH_BED,
        )
        return sorted(((member.value, member.label) for member in members), key=lambda choice: normalize(choice[1]))

    @classmethod
    def choices_for_statut_animal(cls, statut_animal):
        if statut_animal == StatutAnimal.DETENU:
            return cls.choices_detenu
        return cls.choices_sauvage


class ContexteSuspicion(models.TextChoices):
    INVESTIGATION_CAS_HUMAIN = auto(), "Investigation cas humain"
    PROPHYLAXIE = auto(), "Prophylaxie"


class HumanInvolved(models.TextChoices):
    OUI = auto(), "Oui"
    NON = auto(), "Non"
    NE_SAIS_PAS = auto(), "Je ne sais pas"


class TypeDetenteur(models.TextChoices):
    ETABLISSEMENT = "etablissement", "Établissement"
    PARTICULIER = "particulier", "Particulier"


@reversion.register()
class EvenementAnimal(AllowsSoftDeleteMixin, WithNumeroMixin, AllowModificationMixin, models.Model):
    objects = EvenementAnimalManager()

    # Common fields for event handling
    statut_evenement = models.CharField(
        max_length=100,
        choices=StatutEvenement.choices,
        verbose_name="Statut de l'événement",
        null=False,
    )
    date_statut_changed = models.DateField(verbose_name="Date à prendre en compte pour le changement de statut")
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_publication = models.DateTimeField(verbose_name="Date de publication", blank=True, null=True)
    decert_id = models.CharField(max_length=255, verbose_name="N° de la fiche dans DECERT", blank=True)

    # Fields that determines the evenement global setup
    maladie = models.ForeignKey(Maladie, on_delete=models.PROTECT, related_name="cases", null=False)
    espece = models.ForeignKey(Espece, on_delete=models.PROTECT, related_name="cases", null=False)
    statut_animal = models.CharField(
        max_length=100,
        choices=StatutAnimal.choices,
        verbose_name="Statut de l'animal",
        null=False,
    )

    # Détenteur block
    numero_identifiant_etablissement = models.CharField(
        max_length=255, verbose_name="N° identifiant", blank=False, null=True
    )
    raison_sociale_etablissement = models.CharField(
        max_length=100, verbose_name="Raison sociale", blank=True, null=True
    )
    departement_etablissement = models.ForeignKey(
        "core.Departement",
        on_delete=models.PROTECT,
        verbose_name="Département",
        blank=True,
        null=True,
        related_name="sa_evenements_etablissements",
    )
    autre_identifiant_etablissement = models.CharField(
        max_length=255, verbose_name="Autre identifiant / Numagrit", blank=True, null=True
    )
    adresse_lieu_dit_etablissement = models.CharField(max_length=255, verbose_name="Adresse ou lieu-dit", blank=True)
    code_insee_etablissement = models.CharField(
        max_length=5,
        blank=True,
        verbose_name="Code INSEE",
        validators=[
            RegexValidator(
                regex="^[0-9]{5}$",
                message="Le code INSEE doit contenir exactement 5 chiffres",
                code="invalid_code_insee",
            ),
        ],
    )
    siret_etablissement = models.CharField(
        max_length=14,
        verbose_name="SIRET",
        blank=True,
        validators=[
            RegexValidator(
                regex="^[0-9]{14}$",
                message="Le SIRET doit contenir exactement 14 chiffres",
                code="invalid_siret",
            ),
        ],
    )
    commune_etablissement = models.CharField(max_length=100, verbose_name="Commune", blank=True)
    pays_etablissement = CountryField(null=True, blank=True)

    nom_particulier = models.CharField(max_length=255, verbose_name="Nom", null=True)
    prenom_particulier = models.CharField(max_length=255, blank=True, verbose_name="Prénom")
    adresse_particulier = models.CharField(max_length=255, verbose_name="Adresse", blank=True)
    commune_particulier = models.CharField(max_length=100, verbose_name="Commune", blank=True)
    departement_particulier = models.ForeignKey(
        "core.Departement",
        on_delete=models.PROTECT,
        verbose_name="Département",
        blank=True,
        null=True,
        related_name="sa_evenements_particuliers",
    )
    code_insee_particulier = models.CharField(
        max_length=5,
        blank=True,
        verbose_name="Code INSEE",
        validators=[
            RegexValidator(
                regex="^[0-9]{5}$",
                message="Le code INSEE doit contenir exactement 5 chiffres",
                code="invalid_code_insee",
            ),
        ],
    )
    email_particulier = models.EmailField(blank=True, verbose_name="Courriel")
    telephone_particulier = models.CharField(max_length=20, blank=True, verbose_name="Numéro de téléphone")

    # Localisation block
    adresse_lieu_dit = models.CharField(max_length=255, verbose_name="Adresse ou lieu-dit", blank=True)
    commune = models.CharField(max_length=100, verbose_name="Commune", blank=True)
    code_insee = models.CharField(
        max_length=5,
        blank=True,
        verbose_name="Code INSEE de la commune",
        validators=[
            RegexValidator(
                regex="^[0-9]{5}$",
                message="Le code INSEE doit contenir exactement 5 chiffres",
                code="invalid_code_insee",
            ),
        ],
    )
    numero_identifiant = models.CharField(
        max_length=255,
        verbose_name="Identifiant parcelle, culture",
        blank=True,
    )
    type_lieu = models.CharField(
        max_length=100,
        choices=TypeLieu.choices,
        verbose_name="Type de lieu",
        null=False,
    )
    coordinates = PointField(verbose_name="Coordonnées", null=False)

    # Contexte de la suspicion
    context_suspicion = models.CharField(
        max_length=100,
        choices=ContexteSuspicion.choices,
        verbose_name="Contexte de la suspicion",
        null=True,
        blank=True,
    )
    date_first_symptoms = models.DateField(verbose_name="Date d'apparition des éventuels 1ers symptômes", null=True)
    human_involved = models.CharField(
        max_length=100,
        choices=HumanInvolved.choices,
        verbose_name="Humains exposés pour lesquels des actions sont engagées ?",
        null=True,
        blank=True,
    )
    description = models.TextField(verbose_name="Description de la situation", blank=True)

    # Mesures
    date_apms = models.DateField(verbose_name="Date APMS", null=True, blank=True)
    date_apdi = models.DateField(verbose_name="Date APDI", null=True, blank=True)
    date_levee = models.DateField(verbose_name="Date levée APMS ou APDI", null=True, blank=True)

    date_d_zero = models.DateField(verbose_name="Date D zéro", null=True, blank=True)
    date_nd1 = models.DateField(verbose_name="Date ND1", null=True, blank=True)
    date_nd2 = models.DateField(verbose_name="Date ND2", null=True, blank=True)

    # Adis
    foyer = models.CharField(
        max_length=100,
        choices=Foyer.choices,
        verbose_name="Foyer",
        blank=True,
    )
    numero_adis = models.CharField(max_length=255, verbose_name="Numéro ADIS", blank=True)
    date_notification_adis = models.DateField(
        verbose_name="Date de notification ADIS",
        null=True,
        blank=True,
    )
    date_cloture_adis = models.DateField(
        verbose_name="Date clôture ADIS",
        null=True,
        blank=True,
    )
    effectif_retenu = models.IntegerField(
        verbose_name="Effectif retenu notification ADIS",
        null=True,
        blank=True,
    )
    origine_infection = models.CharField(
        max_length=100,
        choices=OrigineInfection.choices,
        verbose_name="Origine de l'infection",
        blank=True,
    )
    mesures_controle = ArrayField(
        models.CharField(max_length=255, choices=MesureDeControle.choices),
        default=list,
        blank=True,
    )

    @classmethod
    def _get_annee_and_numero(cls, acronym):
        annee_courante = datetime.datetime.now().year
        last_fiche = (
            cls._base_manager.filter(numero_annee=annee_courante, maladie__acronym=acronym)
            .select_for_update()
            .order_by("-numero_evenement")
            .first()
        )
        numero_evenement = last_fiche.numero_evenement + 1 if last_fiche else 1
        return annee_courante, numero_evenement

    @property
    def numero(self):
        return f"{self.maladie.acronym}-{self.numero_annee}.{self.numero_evenement}"

    def __str__(self):
        return self.numero

    def save(self, *args, **kwargs):
        if not self.numero_annee and not self.numero_evenement:
            annee, numero = EvenementAnimal._get_annee_and_numero(self.maladie.acronym)
            self.numero_annee = annee
            self.numero_evenement = numero
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("sa:evenement-animal-details", kwargs={"pk": self.pk})

    @property
    def latest_version(self):
        return (
            Version.objects.get_for_object(self)
            .select_related("revision")
            .select_related("revision__user__agent__structure")
            .first()
        )

    @property
    def show_mesures_block(self):
        return self.maladie.needs_arrete

    def get_publish_success_message(self):
        return "Évènement publié avec succès"

    @property
    def mesures_controle_labels(self):
        return ", ".join(MesureDeControle(d).label for d in self.mesures_controle)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        ~models.Q(numero_identifiant_etablissement="")
                        & models.Q(numero_identifiant_etablissement__isnull=False)
                        & (models.Q(nom_particulier="") | models.Q(nom_particulier__isnull=True))
                    )
                    | (
                        (
                            models.Q(numero_identifiant_etablissement="")
                            | models.Q(numero_identifiant_etablissement__isnull=True)
                        )
                        & ~models.Q(nom_particulier="")
                        & models.Q(nom_particulier__isnull=False)
                    )
                ),
                name="evenementanimal_detenteur_etablissement_or_particulier",
                violation_error_message=(
                    "Un détenteur établissement ou un détenteur particulier doit être renseigné (l'un ou l'autre)"
                ),
            ),
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(statut_animal=StatutAnimal.DETENU)
                        & models.Q(type_lieu__in=[value for value, _ in TypeLieu.choices_detenu])
                    )
                    | (
                        models.Q(statut_animal=StatutAnimal.SAUVAGE)
                        & models.Q(type_lieu__in=[value for value, _ in TypeLieu.choices_sauvage])
                    )
                ),
                name="evenementanimal_type_lieu_consistent_with_statut_animal",
                violation_error_message="Le type de lieu n'est pas compatible avec le statut de l'animal sélectionné",
            ),
            models.CheckConstraint(
                condition=(
                    (Q(date_d_zero__isnull=True) | Q(date_nd1__isnull=True) | Q(date_d_zero__lte=F("date_nd1")))
                    & (Q(date_nd1__isnull=True) | Q(date_nd2__isnull=True) | Q(date_nd1__lte=F("date_nd2")))
                    & (Q(date_d_zero__isnull=True) | Q(date_nd2__isnull=True) | Q(date_d_zero__lte=F("date_nd2")))
                ),
                name="evenementanimal_dates_desinfection_order",
                violation_error_message="Les dates D0, ND1 et ND2 doivent respecter l'ordre D0 ≤ ND1 ≤ ND2.",
            ),
        ]
