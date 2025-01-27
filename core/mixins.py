from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models, transaction
from django.urls import reverse

from core.forms import DocumentUploadForm, DocumentEditForm
from .constants import BSV_STRUCTURE, MUS_STRUCTURE
from .filters import DocumentFilter
from core.models import Document, LienLibre, Contact, Message, Visibilite, Structure
from .notifications import notify_message
from .redirect import safe_redirect


class WithDocumentUploadFormMixin:
    def get_object_linked_to_document(self):
        raise NotImplementedError

    def get_redirect_url_after_upload(self):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context["document_form"] = DocumentUploadForm(obj=obj, next=obj.get_absolute_url())
        return context


class WithDocumentListInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = Document.objects.for_fiche(self.get_object()).prefetch_related("created_by_structure")
        document_filter = DocumentFilter(self.request.GET, queryset=documents)
        for document in document_filter.qs:
            document.edit_form = DocumentEditForm(instance=document)
        context["document_filter"] = document_filter
        return context


class WithMessagesListInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message_list"] = (
            self.get_object()
            .messages.all()
            .prefetch_related(
                "recipients__structure", "recipients__agent", "recipients_copy", "sender__agent", "documents"
            )
        )
        return context


class WithContactListInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()

        structures_fin_suivi_ids = (
            Structure.objects.filter(contact__finsuivicontact__in=obj.fin_suivi.all())
            .values_list("id", flat=True)
            .distinct()
        )

        context["contacts_agents"] = [
            {
                "contact": contact,
                "is_in_fin_suivi": contact.agent.structure_id in structures_fin_suivi_ids,
            }
            for contact in obj.contacts.agents_only()
            .prefetch_related("agent__structure")
            .services_deconcentres_first()
            .order_by_structure_and_name()
        ]

        context["contacts_structures"] = [
            {
                "contact": contact,
                "is_in_fin_suivi": contact.structure_id in structures_fin_suivi_ids,
            }
            for contact in obj.contacts.structures_only()
            .services_deconcentres_first()
            .order_by_structure_and_niveau2()
            .select_related("structure")
        ]

        context["content_type"] = ContentType.objects.get_for_model(obj)
        return context


class WithFreeLinksListInContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["free_links_list"] = LienLibre.objects.for_object(self.get_object())
        return context


class AllowsSoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)

    def can_user_delete(self, user):
        raise NotImplementedError

    def soft_delete(self, user):
        if not self.can_user_delete(user):
            raise PermissionDenied
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True


class IsActiveMixin(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AllowACNotificationMixin(models.Model):
    is_ac_notified = models.BooleanField(default=False)

    def can_notifiy(self, user):
        return not self.is_ac_notified and not self.is_draft and not user.agent.structure.is_ac

    def _add_bsv_and_mus_to_contacts(self):
        bsv_contact = Contact.objects.get(structure__niveau2=BSV_STRUCTURE)
        mus_contact = Contact.objects.get(structure__niveau2=MUS_STRUCTURE)
        self.contacts.add(bsv_contact, mus_contact)

    def notify_ac(self, user):
        if not self.can_notifiy(user):
            raise ValidationError("Vous ne pouvez pas notifier cet objet à l'AC")

        self.is_ac_notified = True
        message = Message(
            message_type=Message.NOTIFICATION_AC,
            title="Notification à l'AC",
            content="L'administration a été notifiée de cette fiche.",
            sender=user.agent.contact_set.get(),
            content_object=self,
        )

        try:
            notify_message(message)
            with transaction.atomic():
                self.save()
                message.save()
                self._add_bsv_and_mus_to_contacts()
        except ValidationError as e:
            raise ValidationError(f"Une erreur s'est produite lors de la notification : {e.message}")

    class Meta:
        abstract = True


class WithMessageUrlsMixin:
    @property
    def add_message_url(self):
        content_type = ContentType.objects.get_for_model(self)
        return reverse("message-add", kwargs={"obj_type_pk": content_type.pk, "obj_pk": self.pk})


class WithVisibiliteMixin(models.Model):
    visibilite = models.CharField(
        max_length=100,
        choices=Visibilite,
        default=Visibilite.LOCALE,
    )
    allowed_structures = models.ManyToManyField(Structure, related_name="allowed_structures")

    class Meta:
        abstract = True

    @property
    def is_visibilite_nationale(self):
        return self.visibilite == Visibilite.NATIONALE

    @property
    def is_visibilite_limitee(self):
        return self.visibilite == Visibilite.LIMITEE

    @property
    def is_visibilite_locale(self):
        return self.visibilite == Visibilite.LOCALE

    def can_update_visibilite(self, user):
        raise NotImplementedError

    def can_user_access(self, user):
        """Vérifie si l'utilisateur peut accéder à la fiche de détection."""
        if self.is_visibilite_nationale:
            return True
        if user.agent.is_in_structure(self.createur):
            return True
        if not self.is_draft and user.agent.structure.is_mus_or_bsv:
            return True
        if self.is_visibilite_limitee and not self.is_draft and user.agent.structure in self.allowed_structures.all():
            return True
        return False

    def save(self, *args, **kwargs):
        if self.pk:
            if self.is_visibilite_limitee and self.allowed_structures.count() == 0:
                raise ValidationError("Vous ne pouvez pas avoir une visibilitée limitée sans structure sélectionnée.")
            if not self.is_visibilite_limitee and self.allowed_structures.count() != 0:
                raise ValidationError(
                    "Vous ne pouvez pas avoir des structures autorisée dans un autre cas que la visibilitée limitée."
                )
        super().save(*args, **kwargs)


class WithEtatMixin(models.Model):
    class Etat(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        EN_COURS = "en_cours", "En cours"
        CLOTURE = "cloture", "Clôturé"

    etat = models.CharField(max_length=100, choices=Etat, verbose_name="État de l'événement", default=Etat.BROUILLON)

    class Meta:
        abstract = True

    def cloturer(self):
        self.etat = self.Etat.CLOTURE
        self.save()

    def publish(self):
        self.etat = self.Etat.EN_COURS
        self.save()

    @property
    def is_draft(self):
        return self.etat == self.Etat.BROUILLON

    def can_publish(self, user):
        return user.agent.is_in_structure(self.createur) if self.is_draft else False

    def can_be_cloturer_by(self, user):
        return not self.is_draft and not self.is_already_cloturer() and user.agent.structure.is_ac

    def is_already_cloturer(self):
        return self.etat == self.Etat.CLOTURE


class WithFreeLinkIdsMixin:
    @property
    def free_link_ids(self):
        content_type = ContentType.objects.get_for_model(self)
        links = LienLibre.objects.for_object(self).select_related("content_type_2", "content_type_1")
        link_ids = []
        for link in links:
            if link.object_id_1 == self.id and link.content_type_1 == content_type:
                link_ids.append(f"{link.content_type_2.pk}-{link.object_id_2}")
            else:
                link_ids.append(f"{link.content_type_1.pk}-{link.object_id_1}")
        return link_ids


class CanUpdateVisibiliteRequiredMixin:
    """
    Mixin pour vérifier que l'utilisateur connecté a le droit de modifier la visibilité.
    """

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.can_update_visibilite(request.user):
            messages.error(request, "Vous n'avez pas les droits pour modifier la visibilité de cet objet.")
            return safe_redirect(self.object.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)


class PreventActionIfVisibiliteBrouillonMixin:
    """
    Mixin pour empêcher des actions sur des objets ayant la visibilité 'brouillon'.
    """

    def get_fiche_object(self):
        raise NotImplementedError("Vous devez implémenter la méthode `get_fiche_object` pour ce mixin.")

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_fiche_object()
        if obj.is_draft:
            messages.error(request, "Action impossible car la fiche est en brouillon")
            return safe_redirect(request.POST.get("next") or obj.get_absolute_url() or "/")

        return super().dispatch(request, *args, **kwargs)
