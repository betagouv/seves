from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator
from django.db import models, transaction


class WithBlocCommunFieldsMixin(models.Model):
    fin_suivi = GenericRelation("core.FinSuiviContact")
    documents = GenericRelation("core.Document")
    messages = GenericRelation("core.Message")
    contacts = models.ManyToManyField("core.Contact", verbose_name="Contacts", blank=True)

    class Meta:
        abstract = True

    def get_contacts_structures_not_in_fin_suivi(self):
        contacts_structure = self.contacts.exclude(structure__isnull=True).select_related("structure")
        fin_suivi_contacts_ids = self.fin_suivi.values_list("contact", flat=True)
        return contacts_structure.exclude(id__in=fin_suivi_contacts_ids)

    def get_crdi_form(self):
        raise NotImplementedError

    def add_fin_suivi(self, structure, made_by):
        from core.models import Contact, FinSuiviContact
        from core.notifications import notify_fin_de_suivi

        with transaction.atomic():
            object = FinSuiviContact(
                content_object=self,
                contact=Contact.objects.get(structure=structure),
            )
            object._user = made_by
            object.save()
            notify_fin_de_suivi(self, structure)

    def remove_fin_suivi(self, user):
        from core.models import Contact, FinSuiviContact

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


class BasePermissionMixin:
    def _user_can_interact(self, user):
        raise NotImplementedError


class WithDocumentPermissionMixin(BasePermissionMixin):
    def can_add_document(self, user):
        return self._user_can_interact(user)

    def can_update_document(self, user):
        return self._user_can_interact(user)

    def can_delete_document(self, user):
        return self._user_can_interact(user)

    def can_download_document(self, user):
        return self.can_user_access(user)


class WithFicheDocumentPermissionMixin(WithDocumentPermissionMixin):
    def _assert_etat(self):
        from core.mixins import WithEtatMixin

        return self.etat != WithEtatMixin.Etat.BROUILLON

    def can_add_document(self, user):
        return super().can_add_document(user) and self._assert_etat()

    def can_update_document(self, user):
        return super().can_update_document(user) and self._assert_etat()

    def can_delete_document(self, user):
        return super().can_delete_document(user) and self._assert_etat()


class WithContactPermissionMixin(BasePermissionMixin):
    def can_add_agent(self, user):
        return self._user_can_interact(user)

    def can_add_structure(self, user):
        return self._user_can_interact(user)

    def can_delete_contact(self, user):
        return self._user_can_interact(user)


class WithLocalisableMixin(models.Model):
    commune = models.CharField(max_length=100, verbose_name="Commune", blank=True)
    code_insee = models.CharField(
        max_length=5,
        blank=True,
        verbose_name="Code INSEE de la commune",
        validators=[
            RegexValidator(
                regex=r"^(?:\d{5}|2A\d{3}|2B\d{3})$",
                message="Le code INSEE doit être valide",
                code="invalid_code_insee",
            ),
        ],
    )
    code_postal = models.CharField(
        max_length=5,
        blank=True,
        verbose_name="Code postal de la commune",
        validators=[
            RegexValidator(
                regex=r"^(?:\d{5})$",
                message="Le code postal doit être valide",
                code="invalid_code_postal",
            ),
        ],
    )
    departement = models.ForeignKey(
        "core.Departement",
        on_delete=models.PROTECT,
        verbose_name="Département",
        related_name="%(app_label)s_%(class)s_set",
        blank=True,
        null=True,
    )

    @property
    def address_summary(self):
        value = self.commune_and_cp or ""
        if self.departement:
            departement_numero = "" if self.code_postal else f" - {self.departement.numero}"
            value += f" | {departement_numero}{self.departement.nom}"
        return value

    @property
    def commune_and_cp(self):
        value = ""
        if self.commune:
            code_postal = f" ({self.code_postal})" if self.code_postal else ""
            value = f"{self.commune}{code_postal}"
        return value

    class Meta:
        abstract = True


class WithLastUpdatedDatetime(models.Model):
    last_updated = models.DateTimeField(
        db_index=True,
        null=True,
        blank=True,
        verbose_name="Date de dernière mise à jour",
    )

    class Meta:
        abstract = True


def update_last_updated_on_revision(cls):
    cls._update_last_updated_on_revision = True
    return cls
