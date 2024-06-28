from django.db import models


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
