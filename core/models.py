from django.db import models
from django.conf import settings


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
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # TODO handle deleted_by and date_deletion at some point in the process
    # TODO should we use models Casacade here ? Decide what to do