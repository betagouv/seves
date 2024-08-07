from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db.models import Q

from django.contrib.auth import get_user_model
from .managers import DocumentQueryset, ContactQueryset

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

    @property
    def name_with_structure(self):
        return f"{self.structure} [{self.nom} {self.prenom}]"


class Structure(models.Model):
    class Meta:
        verbose_name = "Structure"
        verbose_name_plural = "Structures"
        ordering = ["niveau1", "niveau2"]

    niveau1 = models.CharField(max_length=255)
    niveau2 = models.CharField(max_length=255, blank=True)
    libelle = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.libelle


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
                check=Q(structure__isnull=False) | Q(agent__isnull=False), name="contact_has_structure_or_agent"
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


class Document(models.Model):
    DOCUMENT_AUTRE = "autre"
    DOCUMENT_CARTOGRAPHIE = "cartographie"
    DOCUMENT_TYPE_CHOICES = ((DOCUMENT_CARTOGRAPHIE, "Cartographie"), (DOCUMENT_AUTRE, "Autre document"))

    nom = models.CharField(max_length=256)
    description = models.TextField()
    document_type = models.CharField(max_length=100, choices=DOCUMENT_TYPE_CHOICES, verbose_name="Type de document")
    file = models.FileField(upload_to="")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name="documents_created")
    created_by_structure = models.ForeignKey(Structure, on_delete=models.PROTECT, related_name="documents_created")
    deleted_by = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name="documents_deleted", null=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    objects = DocumentQueryset.as_manager()

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
    FIN_INTERVENTION = "fin d'intervention"
    MESSAGE_TYPE_CHOICES = (
        (MESSAGE, "Message"),
        (NOTE, "Note"),
        (POINT_DE_SITUATION, "Point de situation"),
        (DEMANDE_INTERVENTION, "Demande d'intervention"),
        (COMPTE_RENDU, "Compte rendu sur demande d'intervention"),
        (FIN_INTERVENTION, "Fin d'intervention"),
    )
    TYPES_TO_FEMINIZE = (NOTE, DEMANDE_INTERVENTION, FIN_INTERVENTION)
    TYPES_WITHOUT_RECIPIENTS = (NOTE, POINT_DE_SITUATION, FIN_INTERVENTION)

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

    def get_absolute_url(self):
        return reverse("message-view", kwargs={"pk": self.pk})
