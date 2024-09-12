from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.core.validators import RegexValidator
import datetime

from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse

from core.mixins import AllowsSoftDeleteMixin
from core.models import Document, Message, Contact, Structure, FinSuiviContact
from sv.managers import FicheDetectionManager


class NumeroFiche(models.Model):
    class Meta:
        unique_together = ("annee", "numero")
        verbose_name = "Numéro de fiche"
        verbose_name_plural = "Numéros de fiche"
        db_table = "sv_numero_fiche"

    annee = models.IntegerField(verbose_name="Année")
    numero = models.IntegerField(verbose_name="Numéro")

    def __str__(self):
        return f"{self.annee}.{self.numero}"

    def _save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @classmethod
    @transaction.atomic  # Assure que la méthode est exécutée dans une transaction pour éviter les race conditions
    def get_next_numero(cls):
        annee_courante = datetime.datetime.now().year
        last_fiche = cls.objects.filter(annee=annee_courante).order_by("-numero").first()

        # Si une fiche existe déjà pour cette année
        # On incrémente le numéro
        # Si aucune fiche n'existe pour cette année
        # On réinitialise le numéro à 1
        if last_fiche is not None:
            numero = last_fiche.numero + 1
        else:
            numero = 1

        new_fiche = cls(annee=annee_courante, numero=numero)
        new_fiche._save()
        return new_fiche


class OrganismeNuisible(models.Model):
    class Meta:
        verbose_name = "Organisme nuisible"
        verbose_name_plural = "Organismes nuisibles"
        db_table = "sv_organisme_nuisible"

    code_oepp = models.CharField(verbose_name="Code OEPP")
    libelle_court = models.CharField(max_length=255, verbose_name="Nom")

    def __str__(self):
        return self.libelle_court


class StatutReglementaire(models.Model):
    class Meta:
        verbose_name = "Statut règlementaire de l'organisme"
        verbose_name_plural = "Statuts règlementaires de l'organisme"
        db_table = "sv_statut_reglementaire"

    code = models.CharField(max_length=10, verbose_name="Code")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")

    def __str__(self):
        return self.libelle


class Contexte(models.Model):
    class Meta:
        verbose_name = "Contexte"
        verbose_name_plural = "Contextes"

    nom = models.CharField(max_length=100, verbose_name="Nom")

    def __str__(self):
        return self.nom


class Region(models.Model):
    class Meta:
        verbose_name = "Région"
        verbose_name_plural = "Régions"
        ordering = ["nom"]

    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)

    def __str__(self):
        return self.nom


class Departement(models.Model):
    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ["numero"]

    numero = models.CharField(max_length=3, verbose_name="Numéro", unique=True)
    nom = models.CharField(max_length=100, verbose_name="Nom", unique=True)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, verbose_name="Région")

    def __str__(self):
        return f"{self.numero} - {self.nom}"


class Lieu(models.Model):
    class Meta:
        verbose_name = "Lieu"
        verbose_name_plural = "Lieux"

    fiche_detection = models.ForeignKey(
        "FicheDetection",
        on_delete=models.CASCADE,
        verbose_name="Fiche de détection",
        related_name="lieux",
    )
    nom = models.CharField(max_length=100, verbose_name="Nom", blank=True)
    wgs84_longitude = models.FloatField(verbose_name="Longitude WGS84", blank=True, null=True)
    wgs84_latitude = models.FloatField(verbose_name="Latitude WGS84", blank=True, null=True)
    lambert93_latitude = models.FloatField(verbose_name="Latitude Lambert 93", blank=True, null=True)
    lambert93_longitude = models.FloatField(verbose_name="Longitude Lambert 93", blank=True, null=True)
    adresse_lieu_dit = models.CharField(max_length=100, verbose_name="Adresse ou lieu-dit", blank=True)
    commune = models.CharField(max_length=100, verbose_name="Commune")
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
    departement = models.ForeignKey(
        Departement,
        on_delete=models.PROTECT,
        verbose_name="Département",
        blank=True,
        null=True,
    )
    is_etablissement = models.BooleanField(verbose_name="Établissement", default=False)
    nom_etablissement = models.CharField(max_length=100, verbose_name="Nom établissement", blank=True)
    activite_etablissement = models.CharField(max_length=100, verbose_name="Activité établissement", blank=True)
    pays_etablissement = models.CharField(max_length=100, verbose_name="Pays établissement", blank=True)
    raison_sociale_etablissement = models.CharField(
        max_length=100, verbose_name="Raison sociale établissement", blank=True
    )
    adresse_etablissement = models.CharField(max_length=100, verbose_name="Adresse établissement", blank=True)
    siret_etablissement = models.CharField(max_length=100, verbose_name="SIRET établissement", blank=True)
    type_exploitant_etablissement = models.ForeignKey(
        "TypeExploitant",
        on_delete=models.PROTECT,
        verbose_name="Type d'exploitant établissement",
        blank=True,
        null=True,
    )
    position_chaine_distribution_etablissement = models.ForeignKey(
        "PositionChaineDistribution",
        on_delete=models.PROTECT,
        verbose_name="Position dans la chaîne de distribution établissement",
        blank=True,
        null=True,
    )
    code_inpp_etablissement = models.CharField(max_length=50, verbose_name="Code INPP", blank=True)

    def __str__(self):
        return str(self.id)


class StatutEtablissement(models.Model):
    class Meta:
        verbose_name = "Statut de l'établissement"
        verbose_name_plural = "Statuts de l'établissement"
        db_table = "sv_statut_etablissement"

    libelle = models.CharField(max_length=100, verbose_name="Libellé")

    def __str__(self):
        return self.libelle


class TypeExploitant(models.Model):
    class Meta:
        verbose_name = "Type d'exploitant"
        verbose_name_plural = "Types d'exploitant"
        db_table = "sv_type_exploitant"

    libelle = models.CharField(max_length=100, verbose_name="Libellé")

    def __str__(self):
        return self.libelle


class PositionChaineDistribution(models.Model):
    class Meta:
        verbose_name = "Position dans la chaîne de distribution"
        verbose_name_plural = "Positions dans la chaîne de distribution"
        db_table = "sv_position_chaine_distribution"

    libelle = models.CharField(max_length=100, verbose_name="Libellé")

    def __str__(self):
        return self.libelle


class StructurePreleveur(models.Model):
    class Meta:
        verbose_name = "Structure préleveur"
        verbose_name_plural = "Structures préleveur"
        db_table = "sv_structure_preleveur"
        ordering = ["nom"]

    nom = models.CharField(max_length=100, verbose_name="Nom")

    def __str__(self):
        return self.nom


class SiteInspection(models.Model):
    class Meta:
        verbose_name = "Site d'inspection"
        verbose_name_plural = "Sites d'inspection"
        db_table = "sv_site_inspection"

    nom = models.CharField(max_length=100, verbose_name="Nom")

    def __str__(self):
        return self.nom


class MatricePrelevee(models.Model):
    class Meta:
        verbose_name = "Matrice prélevée"
        verbose_name_plural = "Matrices prélevées"
        db_table = "sv_matrice_prelevee"

    libelle = models.CharField(max_length=100, verbose_name="Libellé")

    def __str__(self):
        return self.libelle


class EspeceEchantillon(models.Model):
    class Meta:
        verbose_name = "Espèce de l'échantillon"
        verbose_name_plural = "Espèces de l'échantillon"
        db_table = "sv_espece_echantillon"

    code_oepp = models.CharField(max_length=100, verbose_name="Code OEPP", unique=True)
    libelle = models.CharField(max_length=100, verbose_name="Libellé")

    def __str__(self):
        return self.libelle


class LaboratoireAgree(models.Model):
    class Meta:
        verbose_name = "Laboratoire agréé"
        verbose_name_plural = "Laboratoires agréés"
        db_table = "sv_laboratoire_agree"
        ordering = ["nom"]

    nom = models.CharField(max_length=100, verbose_name="Nom")

    def __str__(self):
        return self.nom


class LaboratoireConfirmationOfficielle(models.Model):
    class Meta:
        verbose_name = "Laboratoire de confirmation officielle"
        verbose_name_plural = "Laboratoires de confirmation officielle"
        db_table = "sv_laboratoire_confirmation_officielle"
        ordering = ["nom"]

    nom = models.CharField(max_length=100, verbose_name="Nom")

    def __str__(self):
        return self.nom


class Prelevement(models.Model):
    class Resultat(models.TextChoices):
        DETECTE = "detecte", "Détecté"
        NON_DETECTE = "non_detecte", "Non détecté"

    class Meta:
        verbose_name = "Prélèvement"
        verbose_name_plural = "Prélèvements"
        db_table = "sv_prelevement"

    lieu = models.ForeignKey(Lieu, on_delete=models.CASCADE, verbose_name="Lieu", related_name="prelevements")
    structure_preleveur = models.ForeignKey(
        StructurePreleveur, on_delete=models.PROTECT, verbose_name="Structure préleveur"
    )
    numero_echantillon = models.CharField(max_length=100, verbose_name="Numéro d'échantillon", blank=True)
    date_prelevement = models.DateField(verbose_name="Date de prélèvement", blank=True, null=True)
    site_inspection = models.ForeignKey(
        SiteInspection,
        on_delete=models.PROTECT,
        verbose_name="Site d'inspection",
        blank=True,
        null=True,
    )
    matrice_prelevee = models.ForeignKey(
        MatricePrelevee,
        on_delete=models.PROTECT,
        verbose_name="Matrice prélevée",
        blank=True,
        null=True,
    )
    espece_echantillon = models.ForeignKey(
        EspeceEchantillon,
        on_delete=models.PROTECT,
        verbose_name="Espèce de l'échantillon",
        blank=True,
        null=True,
    )
    is_officiel = models.BooleanField(verbose_name="Prélèvement officiel", default=False)
    numero_phytopass = models.CharField(max_length=100, verbose_name="Numéro Phytopass", blank=True)
    laboratoire_agree = models.ForeignKey(
        "LaboratoireAgree",
        on_delete=models.PROTECT,
        verbose_name="Laboratoire agréé",
        blank=True,
        null=True,
    )
    laboratoire_confirmation_officielle = models.ForeignKey(
        "LaboratoireConfirmationOfficielle",
        on_delete=models.PROTECT,
        verbose_name="Laboratoire de confirmation officielle",
        blank=True,
        null=True,
    )
    resultat = models.CharField(max_length=50, choices=Resultat.choices, verbose_name="Résultat", blank=True)

    def __str__(self):
        return f"Prélèvement n° {self.id}"


class StatutEvenement(models.Model):
    class Meta:
        verbose_name = "Statut de l'événement"
        verbose_name_plural = "Statuts de l'événement"
        db_table = "sv_statut_evenement"

    libelle = models.CharField(max_length=100, verbose_name="Libellé")

    def __str__(self):
        return self.libelle


class Etat(models.Model):
    NOUVEAU = "nouveau"
    EN_COURS = "en cours"
    CLOTURE = "clôturé"

    class Meta:
        verbose_name = "Etat"
        verbose_name_plural = "Etats"
        db_table = "sv_etat"

    libelle = models.CharField(max_length=30, unique=True)

    @classmethod
    def get_etat_initial(cls):
        return cls.objects.get(libelle=cls.NOUVEAU).id

    @classmethod
    def get_etat_cloture(cls):
        return cls.objects.get(libelle=cls.CLOTURE)

    def is_cloture(self):
        return self.libelle == self.CLOTURE

    def __str__(self):
        return self.libelle


class FicheDetection(AllowsSoftDeleteMixin, models.Model):
    class Meta:
        verbose_name = "Fiche détection"
        verbose_name_plural = "Fiches détection"
        db_table = "sv_fiche_detection"

    # Informations générales
    numero = models.OneToOneField(NumeroFiche, on_delete=models.PROTECT, verbose_name="Numéro de fiche")
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    numero_europhyt = models.CharField(max_length=8, verbose_name="Numéro Europhyt", blank=True)
    numero_rasff = models.CharField(max_length=9, verbose_name="Numéro RASFF", blank=True)
    statut_evenement = models.ForeignKey(
        StatutEvenement,
        on_delete=models.PROTECT,
        verbose_name="Statut de l'événement",
        blank=True,
        null=True,
    )

    # Objet de l'événement
    organisme_nuisible = models.ForeignKey(
        OrganismeNuisible,
        on_delete=models.PROTECT,
        verbose_name="OEPP",
        blank=True,
        null=True,
    )
    statut_reglementaire = models.ForeignKey(
        StatutReglementaire,
        on_delete=models.PROTECT,
        verbose_name="Statut règlementaire de l'organisme",
        blank=True,
        null=True,
    )
    contexte = models.ForeignKey(
        Contexte,
        on_delete=models.PROTECT,
        verbose_name="Contexte",
        blank=True,
        null=True,
    )
    date_premier_signalement = models.DateField(verbose_name="Date premier signalement", blank=True, null=True)
    commentaire = models.TextField(verbose_name="Commentaire", blank=True)

    # Mesures de gestion
    mesures_conservatoires_immediates = models.TextField(verbose_name="Mesures conservatoires immédiates", blank=True)
    mesures_consignation = models.TextField(verbose_name="Mesures de consignation", blank=True)
    mesures_phytosanitaires = models.TextField(verbose_name="Mesures phytosanitaires", blank=True)
    mesures_surveillance_specifique = models.TextField(verbose_name="Mesures de surveillance spécifique", blank=True)

    etat = models.ForeignKey(
        Etat, on_delete=models.PROTECT, verbose_name="État de la fiche", default=Etat.get_etat_initial
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    documents = GenericRelation(Document)
    messages = GenericRelation(Message)
    contacts = models.ManyToManyField(Contact, verbose_name="Contacts", blank=True)
    fin_suivi = GenericRelation(FinSuiviContact)

    objects = FicheDetectionManager()

    def get_absolute_url(self):
        return reverse("fiche-detection-vue-detaillee", kwargs={"pk": self.pk})

    def get_content_type_id(self) -> int:
        """Renvoie l'ID du ContentType associé au modèle FicheDetection"""
        return ContentType.objects.get_for_model(self).pk

    def _add_message_url(self, message_type):
        content_type = ContentType.objects.get_for_model(self)
        return reverse(
            "message-add", kwargs={"message_type": message_type, "obj_type_pk": content_type.pk, "obj_pk": self.pk}
        )

    def cloturer(self):
        self.etat = Etat.get_etat_cloture()
        self.save()

    @property
    def add_message_url(self):
        return self._add_message_url(Message.MESSAGE)

    @property
    def add_note_url(self):
        return self._add_message_url(Message.NOTE)

    @property
    def add_point_de_suivi_url(self):
        return self._add_message_url(Message.POINT_DE_SITUATION)

    @property
    def add_demande_intervention_url(self):
        return self._add_message_url(Message.DEMANDE_INTERVENTION)

    @property
    def add_compte_rendu_url(self):
        return self._add_message_url(Message.COMPTE_RENDU)

    @property
    def add_fin_suivi_url(self):
        return self._add_message_url(Message.FIN_SUIVI)

    def __str__(self):
        return str(self.numero)

    def can_be_cloturer_by(self, user):
        return user.agent.structure.is_ac

    def is_already_cloturer(self):
        return self.etat.is_cloture()
