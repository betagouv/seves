from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q, CheckConstraint
from django.utils.translation import gettext_lazy as _

from core.constants import AC_STRUCTURE, MUS_STRUCTURE, BSV_STRUCTURE
from .managers import ContactQueryset, LienLibreQueryset, StructureQueryset, DocumentManager, DocumentQueryset
from .storage import get_timestamped_filename
from .validators import validate_upload_file, AUTHORIZED_EXTENSIONS

User = get_user_model()


class Agent(models.Model):
    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"
        indexes = [
            models.Index(fields=["user"]),
        ]
        ordering = ["nom", "prenom"]

    user = models.OneToOneField(User, on_delete=models.RESTRICT)
    structure = models.ForeignKey("Structure", on_delete=models.RESTRICT)
    structure_complete = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    nom = models.CharField(max_length=255)
    fonction_hierarchique = models.CharField(max_length=255, blank=True)
    complement_fonction = models.TextField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    def is_in_structure(self, structure):
        return self.structure == structure

    @property
    def agent_with_structure(self):
        return f"{self.nom} {self.prenom} ({self.structure})"


class Structure(models.Model):
    class Meta:
        verbose_name = "Structure"
        verbose_name_plural = "Structures"
        ordering = ["niveau1", "niveau2"]

    niveau1 = models.CharField(max_length=255)
    niveau2 = models.CharField(max_length=255, blank=True)
    libelle = models.CharField(max_length=255, blank=True)

    objects = StructureQueryset.as_manager()

    def __str__(self):
        return self.libelle

    @property
    def is_ac(self):
        "Permet de savoir si la structure fait partie de l'administration centrale (AC)"
        return self.niveau1 == AC_STRUCTURE

    @property
    def is_mus_or_bsv(self):
        return self.niveau2 in [MUS_STRUCTURE, BSV_STRUCTURE]


class Contact(models.Model):
    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        indexes = [
            models.Index(fields=["email", "structure", "agent"]),
        ]
        ordering = ["structure", "agent"]
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(structure__isnull=False) & Q(agent__isnull=True))
                    | (Q(structure__isnull=True) & Q(agent__isnull=False))
                ),
                name="contact_has_structure_or_agent",
            ),
        ]

    structure = models.ForeignKey(Structure, on_delete=models.RESTRICT, null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.RESTRICT, null=True, blank=True)
    email = models.EmailField()

    objects = ContactQueryset.as_manager()

    def __str__(self):
        return str(self.structure) if self.structure else str(self.agent)

    @property
    def display_with_agent_unit(self):
        return (
            str(self.structure) if self.structure else f"{self.agent.nom} {self.agent.prenom} ({self.agent.structure})"
        )

    def get_structure_contact(self):
        """Retourne le contact de la structure associée si ce contact est lié à un agent."""
        if self.agent:
            return self.agent.structure.contact_set.first()


class FinSuiviContact(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["content_type", "object_id", "contact"], name="unique_fin_suivi_contact")
        ]

    def __str__(self):
        return f"Fin de suivi de {self.contact} pour la fiche {self.content_type} n° {self.content_object}"

    def clean(self):
        super().clean()
        content_type_model = self.content_type.model
        fiche_model = apps.get_model(self.content_type.app_label, content_type_model)
        fiche_object = fiche_model.objects.get(id=self.object_id)
        if not hasattr(fiche_object, "contacts"):
            raise ValidationError(f"La fiche {fiche_model} liée ne possède pas de relation 'contacts'.")
        if self.contact.agent:
            raise ValidationError("Le contact doit être lié à une structure et non à un agent.")
        if not fiche_object.contacts.filter(id=self.contact.id).exists():
            raise ValidationError(
                "Vous ne pouvez pas signaler la fin de suivi pour cette fiche car votre structure n'est pas dans la liste des contacts."
            )


class Document(models.Model):
    class TypeDocument(models.TextChoices):
        ARRETE = "arrete_prefectoral_ministériel", "Arrêté préfectoral/ministériel"
        AUTRE = "autre", "Autre document"
        CARTOGRAPHIE = "cartographie", "Cartographie"
        CERTIFICAT_PHYTOSANITAIRE = "certificat_phytosanitaire", "Certificat phytosanitaire"
        COMPTE_RENDU_REUNION = "compte_rendu_reunion", "Compte rendu de réunion"
        COURRIER_OFFICIEL = "courrier_officiel", "Courrier officiel"
        DSCE = "dsce", "DSCE"
        FACTURE = "facture", "Facture"
        IMAGE = "image", "Image"
        PASSEPORT_PHYTOSANITAIRE = "passeport_phytosanitaire", "Passeport phytosanitaire"
        RAPPORT_ANALYSE = "rapport_analyse", "Rapport d'analyse"
        RAPPORT_INSPECTION = "rapport_inspection", "Rapport d'inspection"
        REGLEMENTATION = "reglementation", "Réglementation"
        TRANSPORT = "document_de_transport", "Document de transport"
        TRACABILITE = "tracabilité", "Traçabilité"

    nom = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    document_type = models.CharField(max_length=100, choices=TypeDocument.choices, verbose_name="Type de document")
    file = models.FileField(
        upload_to=get_timestamped_filename,
        validators=[validate_upload_file, FileExtensionValidator(AUTHORIZED_EXTENSIONS)],
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name="documents_created")
    created_by_structure = models.ForeignKey(Structure, on_delete=models.PROTECT, related_name="documents_created")
    deleted_by = models.ForeignKey(
        Agent, on_delete=models.PROTECT, related_name="documents_deleted", null=True, blank=True
    )
    is_infected = models.BooleanField(default=None, null=True, verbose_name="Est ce que le fichier est infecté")

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    objects = DocumentManager.from_queryset(DocumentQueryset)()

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.nom} ({self.document_type})"


class Message(models.Model):
    MESSAGE = "message"
    NOTE = "note"
    POINT_DE_SITUATION = "point de situation"
    DEMANDE_INTERVENTION = "demande d'intervention"
    COMPTE_RENDU = "compte rendu sur demande d'intervention"
    FIN_SUIVI = "fin de suivi"
    NOTIFICATION_AC = "notification ac"
    MESSAGE_TYPE_CHOICES = (
        (MESSAGE, "Message"),
        (NOTE, "Note"),
        (POINT_DE_SITUATION, "Point de situation"),
        (DEMANDE_INTERVENTION, "Demande d'intervention"),
        (COMPTE_RENDU, "Compte rendu sur demande d'intervention"),
        (FIN_SUIVI, "Fin de suivi"),
        (NOTIFICATION_AC, "Notification à l'administration centrale"),
    )
    TYPES_TO_FEMINIZE = (NOTE, DEMANDE_INTERVENTION, FIN_SUIVI)
    TYPES_WITHOUT_RECIPIENTS = (NOTE, POINT_DE_SITUATION, FIN_SUIVI)
    TYPES_WITH_LIMITED_RECIPIENTS = (COMPTE_RENDU,)

    message_type = models.CharField(max_length=100, choices=MESSAGE_TYPE_CHOICES)
    title = models.CharField(max_length=512, verbose_name="Titre")
    content = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    sender = models.ForeignKey(Contact, on_delete=models.PROTECT, related_name="messages")
    recipients = models.ManyToManyField(Contact, related_name="messages_recipient")
    recipients_copy = models.ManyToManyField(Contact, related_name="messages_recipient_copy")

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    documents = GenericRelation(Document)

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Message de type {self.message_type}: {self.content[:150]}..."

    def get_fiche_url(self):
        return self.content_object.get_absolute_url()


class LienLibre(models.Model):
    content_type_1 = models.ForeignKey(ContentType, on_delete=models.PROTECT, related_name="relation_1")
    object_id_1 = models.PositiveIntegerField()
    related_object_1 = GenericForeignKey("content_type_1", "object_id_1")

    content_type_2 = models.ForeignKey(ContentType, on_delete=models.PROTECT, related_name="relation_2")
    object_id_2 = models.PositiveIntegerField()
    related_object_2 = GenericForeignKey("content_type_2", "object_id_2")

    objects = LienLibreQueryset.as_manager()

    class Meta:
        constraints = [
            CheckConstraint(
                check=~Q(content_type_1=models.F("content_type_2"), object_id_1=models.F("object_id_2")),
                name="no_self_relation",
            ),
        ]

    def clean(self):
        super().clean()
        if LienLibre.objects.filter(
            content_type_1=self.content_type_1,
            object_id_1=self.object_id_1,
            content_type_2=self.content_type_2,
            object_id_2=self.object_id_2,
        ).exists():
            raise ValidationError("Cette relation existe déjà.")

        if LienLibre.objects.filter(
            content_type_1=self.content_type_2,
            object_id_1=self.object_id_2,
            content_type_2=self.content_type_1,
            object_id_2=self.object_id_1,
        ).exists():
            raise ValidationError("Une relation inverse existe déjà.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class UnitesMesure(models.TextChoices):
    METRE = "m", _("Mètre")
    KILOMETRE = "km", _("Kilomètre")
    HECTARE = "ha", _("Hectare")
    METRE_CARRE = "m2", _("Mètre carré")
    KILOMETRE_CARRE = "km2", _("Kilomètre carré")


class Visibilite(models.TextChoices):
    LOCALE = "locale", "Votre structure et l'administration centrale pourront consulter et modifier la fiche"
    LIMITEE = "limitee", "Les structures de votre choix pourront consulter et modifier la fiche"
    NATIONALE = "nationale", "La fiche sera visible et modifiable par toutes les structures"
