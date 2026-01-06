from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

from core.models import Document, Message, Contact, FinSuiviContact
from core.notifications import notify_fin_de_suivi


class WithBlocCommunFieldsMixin(models.Model):
    fin_suivi = GenericRelation(FinSuiviContact)
    documents = GenericRelation(Document)
    messages = GenericRelation(Message)
    contacts = models.ManyToManyField(Contact, verbose_name="Contacts", blank=True)

    class Meta:
        abstract = True

    def get_contacts_structures_not_in_fin_suivi(self):
        contacts_structure = self.contacts.exclude(structure__isnull=True).select_related("structure")
        fin_suivi_contacts_ids = self.fin_suivi.values_list("contact", flat=True)
        return contacts_structure.exclude(id__in=fin_suivi_contacts_ids)

    def get_crdi_form(self):
        raise NotImplementedError

    def add_fin_suivi(self, structure, made_by):
        with transaction.atomic():
            object = FinSuiviContact(
                content_object=self,
                contact=Contact.objects.get(structure=structure),
            )
            object._user = made_by
            object.save()
            notify_fin_de_suivi(self, structure)

    def remove_fin_suivi(self, user):
        fin_suivi = FinSuiviContact.objects.get(
            object_id=self.id,
            content_type=ContentType.objects.get_for_model(self.__class__),
            contact=Contact.objects.get(structure=user.agent.structure),
        )
        fin_suivi.delete()


class EmailableObjectMixin(models.Model):
    class Meta:
        abstract = True

    def get_short_email_display_name(self):
        raise NotImplementedError

    def get_long_email_display_name(self):
        raise NotImplementedError
