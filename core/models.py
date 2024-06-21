from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


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


class Document(models.Model):
    DOCUMENT_AUTRE = "autre"
    DOCUMENT_TYPE_CHOICES = ((DOCUMENT_AUTRE, "Autre document"),)

    nom = models.CharField(max_length=256)
    description = models.TextField()
    document_type = models.CharField(max_length=100, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to="")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    is_deleted = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.nom} ({self.document_type})"
