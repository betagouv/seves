from typing import Literal

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, When, Value, IntegerField, QuerySet, Q, Manager, OuterRef, Subquery, Func, F, Exists

from core.constants import MUS_STRUCTURE, BSV_STRUCTURE, SERVICE_ACCOUNT_NAME, SSA_STRUCTURES, TIAC_STRUCTURES


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
        return self.filter(Q(agent__user__groups__name__in=groups) | Q(structure__agent__user__groups__name__in=groups))

    def get_mus(self):
        return self.get(structure__niveau2=MUS_STRUCTURE)

    def get_bsv(self):
        return self.get(structure__niveau2=BSV_STRUCTURE)

    def agents_only(self):
        return self.exclude(agent__isnull=True)

    def structures_only(self):
        return self.exclude(structure__isnull=True)

    def with_active_agent(self):
        return self.filter(agent__user__is_active=True)

    def exclude_empty_emails(self):
        return self.exclude(email="")

    def get_ssa_structures(self):
        return self.filter(structure__libelle__in=SSA_STRUCTURES).prefetch_related("structure")

    def get_tiac_structures(self):
        return self.filter(structure__libelle__in=TIAC_STRUCTURES).prefetch_related("structure")

    def can_be_emailed(self):
        return self.exclude_empty_emails().with_active_agent() | self.exclude_empty_emails().structures_only()

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
        return self.filter(agent__user__is_active=True).distinct()

    def can_be_contacted(self):
        return self.has_at_least_one_active_contact().exclude(niveau1=SERVICE_ACCOUNT_NAME).exclude(contact__email="")

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
        return super().get_queryset().filter(is_deleted=False)
