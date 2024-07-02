from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from .managers import DocumentQueryset


class Contact(models.Model):
    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        indexes = [
            models.Index(fields=["structure"]),
            models.Index(fields=["email"]),
        ]

    structure = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    nom = models.CharField(max_length=255)
    email = models.EmailField()
    fonction_hierarchique = models.CharField(max_length=255, blank=True)
    complement_fonction = models.TextField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.structure} - {self.prenom} {self.nom}"


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
    MESSAGE_TYPE_CHOICES = ((MESSAGE, "Message"), (NOTE, "Note"))

    message_type = models.CharField(max_length=100, choices=MESSAGE_TYPE_CHOICES)
    title = models.CharField(max_length=512, verbose_name="Titre")
    content = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

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
