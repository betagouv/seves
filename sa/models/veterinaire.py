from django.core.validators import RegexValidator
from django.db import models


class TypeVeterinaire(models.TextChoices):
    SANITAIRE = "sanitaire", "Sanitaire"
    MANDATE = "mandate", "Mandaté"


class Veterinaire(models.Model):
    evenement = models.ForeignKey(
        "sa.EvenementAnimal", on_delete=models.CASCADE, verbose_name="Événement", related_name="veterinaires"
    )
    type_veterinaire = models.CharField(
        max_length=20,
        choices=TypeVeterinaire.choices,
        default=TypeVeterinaire.SANITAIRE,
        verbose_name="Type de vétérinaire",
    )

    # Structure
    nom_structure = models.CharField(max_length=255, verbose_name="Nom de la structure")
    numero_dpe = models.CharField(max_length=255, blank=True, verbose_name="N° DPE")
    adresse_lieu_dit = models.CharField(max_length=255, blank=True, verbose_name="Adresse ou lieu-dit")
    commune = models.CharField(max_length=100, blank=True, verbose_name="Commune")
    departement = models.ForeignKey(
        "core.Departement",
        on_delete=models.PROTECT,
        verbose_name="Département",
        blank=True,
        null=True,
        related_name="sa_veterinaires",
    )
    code_insee = models.CharField(
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
    telephone_structure = models.CharField(max_length=20, blank=True, verbose_name="Numéro de téléphone")
    courriel_structure = models.EmailField(blank=True, verbose_name="Courriel")

    # Vétérinaire
    nom = models.CharField(max_length=255, blank=True, verbose_name="Nom")
    prenom = models.CharField(max_length=255, blank=True, verbose_name="Prénom")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Numéro de téléphone")
    courriel = models.EmailField(blank=True, verbose_name="Courriel")

    especes = models.ManyToManyField("sa.Espece", related_name="veterinaires", blank=True, verbose_name="Espèces")

    class Meta:
        verbose_name = "Vétérinaire"
        verbose_name_plural = "Vétérinaires"

    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.nom_structure}".strip()
