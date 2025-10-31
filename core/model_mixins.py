from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction

from core.models import Document, Message, Contact, FinSuiviContact


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

    def get_message_form(self):
        raise NotImplementedError

    def get_crdi_form(self):
        raise NotImplementedError

    def add_fin_suivi(self, user):
        with transaction.atomic():
            FinSuiviContact.objects.create(
                content_object=self,
                contact=Contact.objects.get(structure=user.agent.structure),
            )

            Message.objects.create(
                title="Fin de suivi",
                content="Fin de suivi ajoutée automatiquement suite à la clôture de l'événement.",
                sender=user.agent.contact_set.get(),
                sender_structure=user.agent.structure,
                message_type=Message.FIN_SUIVI,
                content_object=self,
            )
