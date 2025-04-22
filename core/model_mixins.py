from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from core.models import Document, Message, Contact, FinSuiviContact


class WithBlocCommunFieldsMixin(models.Model):
    fin_suivi = GenericRelation(FinSuiviContact)
    documents = GenericRelation(Document)
    messages = GenericRelation(Message)
    contacts = models.ManyToManyField(Contact, verbose_name="Contacts", blank=True)

    class Meta:
        abstract = True
