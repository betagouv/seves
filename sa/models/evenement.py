from enum import auto

from django.contrib.gis.db.models import PointField
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse

from core.mixins import WithEtatMixin, WithNumeroMixin
from core.models import Structure
from core.soft_delete_mixins import AllowsSoftDeleteMixin


class Maladie(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.name


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


class TypeLieu(models.TextChoices):
    ABATTOIR = auto(), "Abattoir"
    AUTRE = auto(), "Autre"


class ContexteSuspicion(models.TextChoices):
    INVESTIGATION_CAS_HUMAIN = auto(), "Investigation cas humain"
    PROPHYLAXIE = auto(), "Prophylaxie"


class HumanInvolved(models.TextChoices):
    OUI = auto(), "Oui"
    NON = auto(), "Non"
    NE_SAIS_PAS = auto(), "Je ne sais pas"


class EvenementAnimal(AllowsSoftDeleteMixin, WithNumeroMixin, WithEtatMixin, models.Model):
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
        choices=StatutAnimal.choices,
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

    def save(self, *args, **kwargs):
        if not self.numero_annee and not self.numero_evenement:
            annee, numero = EvenementAnimal._get_annee_and_numero()
            self.numero_annee = annee
            self.numero_evenement = numero
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("sa:evenement-animal-details", kwargs={"numero": self.numero})
