from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Document(models.Model):
    DOCUMENT_AUTRE = "autre"
    DOCUMENT_TYPE_CHOICES = (
        (DOCUMENT_AUTRE, "Autre document"),
    )

    nom = models.CharField(max_length=256)
    description = models.TextField()
    document_type = models.CharField(max_length=100, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    is_deleted = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.nom} ({self.document_type})"

