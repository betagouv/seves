from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, When, Value, IntegerField, QuerySet

from core.constants import MUS_STRUCTURE, BSV_STRUCTURE, AC_STRUCTURE


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

        message_ids = fiche.messages.all().values_list("id", flat=True)
        message_type = ContentType.objects.get_for_model(Message)
        return self.filter(content_type=message_type, object_id__in=message_ids)


class ContactQueryset(QuerySet):
    def with_structure_and_agent(self):
        return self.select_related("structure", "agent")

    def get_mus(self):
        return self.get(structure__niveau2=MUS_STRUCTURE)

    def get_bsv(self):
        return self.get(structure__niveau2=BSV_STRUCTURE)

    def agents_only(self):
        return self.exclude(agent__isnull=True)

    def structures_only(self):
        return self.exclude(structure__isnull=True)

    def services_deconcentres_first(self):
        return self.annotate(
            services_deconcentres_first=Case(
                When(structure__niveau1__exact=AC_STRUCTURE, then=2),
                default=1,
                output_field=IntegerField(),
            )
        )

    def order_by_structure_and_name(self):
        return self.order_by("services_deconcentres_first", "agent__structure__niveau2", "agent__nom")

    def order_by_structure_and_niveau2(self):
        return self.order_by("services_deconcentres_first", "structure__niveau2")
