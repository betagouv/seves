from typing import Literal

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, When, Value, IntegerField, QuerySet, Q, Manager, OuterRef, Subquery, Func, F, Exists
from django.contrib.auth import get_user_model

from core.constants import (
    MUS_STRUCTURE,
    BSV_STRUCTURE,
    SERVICE_ACCOUNT_NAME,
    SSA_STRUCTURES,
    TIAC_STRUCTURES,
    SEVES_STRUCTURE,
)

User = get_user_model()


class DocumentManager(Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(is_infected=True)


class DocumentQueryset(QuerySet):
    def order_list(self):
        return self.annotate(
            custom_order=Case(
                When(is_deleted=False, then=Value(0)),
                When(is_deleted=True, then=Value(1)),
                output_field=IntegerField(),
            )
        ).order_by("custom_order", "-date_creation")

    def for_fiche(self, fiche):
        return (fiche.documents.all() | self.extract_from_fiche_messages(fiche)).order_list()

    def extract_from_fiche_messages(self, fiche):
        from core.models import Message

        message_ids = fiche.messages.exclude(status=Message.Status.BROUILLON).values_list("id", flat=True)
        message_type = ContentType.objects.get_for_model(Message)
        return self.filter(content_type=message_type, object_id__in=message_ids)


class ContactManager(Manager):
    def get_queryset(self):
        return ContactQueryset(self.model, using=self._db)

    def get_emails_in_fin_de_suivi_for_object(self, object):
        from .models import Contact, FinSuiviContact

        content_type = ContentType.objects.get_for_model(object)

        # Remove structure in fin de suivi
        fin_de_suivi = FinSuiviContact.objects.filter(content_type=content_type, object_id=object.id)
        emails_in_fin_de_suivi = set(fin_de_suivi.values_list("contact__email", flat=True))

        # Remove agent in structure in fin de suivi
        emails_in_fin_de_suivi.update(
            Contact.objects.filter(
                agent__isnull=False,
                agent__structure__contact__finsuivicontact__content_type=content_type,
                agent__structure__contact__finsuivicontact__object_id=object.id,
            ).values_list("email", flat=True)
        )
        return emails_in_fin_de_suivi


class ContactQueryset(QuerySet):
    def with_structure_and_agent(self):
        return self.select_related("structure", "agent")

    def for_apps(self, *apps: None | Literal["sv", "ssa"]):
        groups = set()
        for app in apps:
            match app:
                case "sv":
                    groups.add(settings.SV_GROUP)
                case "ssa":
                    groups.add(settings.SSA_GROUP)
        return self.filter(
            Q(agent__user__groups__name__in=groups)
            | Q(structure__agent__user__groups__name__in=groups)
            | Q(structure__force_can_be_contacted=True)
        ).distinct()

    def get_mus(self):
        return self.get(structure__niveau2=MUS_STRUCTURE)

    def get_bsv(self):
        return self.get(structure__niveau2=BSV_STRUCTURE)

    def agents_only(self):
        return self.exclude(agent__isnull=True)

    def agents_with_group(self, group):
        return self.agents_only().filter(agent__user__groups__name__in=[group])

    def structures_only(self):
        return self.exclude(structure__isnull=True)

    def exclude_mus(self):
        return self.exclude(structure__niveau2=MUS_STRUCTURE)

    def with_active_agent(self):
        return self.filter(agent__user__is_active=True)

    def exclude_empty_emails(self):
        return self.exclude(email="")

    def get_ssa_structures(self):
        return self.filter(structure__libelle__in=SSA_STRUCTURES).prefetch_related("structure")

    def get_tiac_structures(self):
        return self.filter(structure__libelle__in=TIAC_STRUCTURES).prefetch_related("structure")

    def can_be_emailed(self):
        return self.exclude_empty_emails().with_active_agent().exclude(
            agent__structure__niveau1=SEVES_STRUCTURE
        ) | self.exclude_empty_emails().structures_only().exclude(structure__niveau1=SEVES_STRUCTURE)

    def order_by_structure_and_name(self):
        return self.order_by("agent__structure__libelle", "agent__nom", "agent__prenom")


class LienLibreQueryset(QuerySet):
    def for_object(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(
            (Q(content_type_1=content_type, object_id_1=obj.id)) | (Q(content_type_2=content_type, object_id_2=obj.id))
        )

    def for_both_objects(self, object_1, object_2):
        content_type_1 = ContentType.objects.get_for_model(object_1)
        content_type_2 = ContentType.objects.get_for_model(object_2)
        link = self.filter(
            content_type_1=content_type_1,
            object_id_1=object_1.id,
            content_type_2=content_type_2,
            object_id_2=object_2.id,
        ).first()
        if link:
            return link

        link = self.filter(
            content_type_2=content_type_1,
            object_id_2=object_1.id,
            content_type_1=content_type_2,
            object_id_1=object_2.id,
        ).first()
        return link


class StructureQueryset(QuerySet):
    def has_at_least_one_active_contact(self):
        return self.filter(Q(agent__user__is_active=True) | Q(force_can_be_contacted=True))

    def can_be_contacted_and_agent_has_group(self, group):
        return (
            self.has_at_least_one_active_contact()
            .exclude(niveau1=SERVICE_ACCOUNT_NAME)
            .exclude(niveau1=SEVES_STRUCTURE)
            .exclude(contact__email="")
            .filter(agent__user__groups__name__in=[group])
            .distinct()
        )

    def can_be_contacted(self):
        base_qs = self.exclude(niveau1=SERVICE_ACCOUNT_NAME).exclude(niveau1=SEVES_STRUCTURE).exclude(contact__email="")
        structures = base_qs.has_at_least_one_active_contact()
        forced_structures = base_qs.filter(force_can_be_contacted=True)
        return (structures | forced_structures).distinct()

    def only_DD(self):
        return self.filter(libelle__startswith="DD").can_be_contacted()


class EvenementManagerMixin:
    def _with_nb_liens_libres(self, model_class):
        from .models import LienLibre

        content_type = ContentType.objects.get_for_model(model_class)

        liens = (
            LienLibre.objects.filter(
                Q(content_type_1=content_type, object_id_1=OuterRef("pk"))
                | Q(content_type_2=content_type, object_id_2=OuterRef("pk"))
            )
            .annotate(count=Func(F("id"), function="Count"))
            .values("count")
        )
        return self.annotate(nb_liens_libre=Subquery(liens))

    def _with_fin_de_suivi(self, contact, model_class):
        from .models import FinSuiviContact

        content_type = ContentType.objects.get_for_model(model_class)
        return self.annotate(
            has_fin_de_suivi=Exists(
                FinSuiviContact.objects.filter(content_type=content_type, object_id=OuterRef("pk"), contact=contact)
            )
        )


class MessageManager(Manager):
    def get_queryset(self):
        return MessagQueryset(self.model, using=self._db).filter(is_deleted=False)


class MessagQueryset(QuerySet):
    def for_user(self, user):
        from core.models import Message

        return self.filter(Q(status=Message.Status.FINALISE) | Q(sender=user.agent.contact_set.get()))

    def optimized_for_list(self):
        return self.select_related("sender__agent__structure", "sender_structure").prefetch_related(
            "recipients__agent",
            "recipients__structure",
            "recipients__agent__structure",
            "documents",
        )

    def search(self, query):
        fields = [
            "sender__agent__prenom",
            "sender__agent__nom",
            "sender_structure__libelle",
            "recipients__agent__prenom",
            "recipients__agent__nom",
            "recipients__structure__libelle",
            "recipients_copy__agent__prenom",
            "recipients_copy__agent__nom",
            "recipients_copy__structure__libelle",
            "title",
            "content",
        ]
        query_object = Q()
        for f in fields:
            query_object |= Q(**{f"{f}__unaccent__icontains": query})

        # Add fields for document
        from .models import Document

        ct = ContentType.objects.get_for_model(self.model)
        doc_qs = (
            Document.objects.filter(content_type=ct)
            .filter(Q(nom__unaccent__icontains=query) | Q(description__unaccent__icontains=query))
            .values("object_id")
        )
        query_object |= Q(pk__in=Subquery(doc_qs))

        return self.filter(query_object).distinct()
