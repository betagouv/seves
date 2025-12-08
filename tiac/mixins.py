from core.mixins import WithOrderingMixin
from tiac.filters import TiacFilter
from tiac.models import EvenementSimple, InvestigationTiac
from queryset_sequence import QuerySetSequence


class WithFilteredListMixin(WithOrderingMixin):
    def get_ordering_fields(self):
        return {
            "numero_evenement": ("numero_annee", "numero_evenement"),
            "createur": "createur__libelle",
            "date_reception": "date_reception",
            "etat": "etat",
        }

    def get_default_order_by(self):
        return "numero_evenement"

    @property
    def get_raw_queryset(self):
        user = self.request.user
        contact = user.agent.structure.contact_set.get()

        evenement_simple_qs = (
            EvenementSimple.objects.select_related("createur")
            .get_user_can_view(user)
            .with_fin_de_suivi(contact)
            .prefetch_related("etablissements")
        )
        investigation_qs = (
            InvestigationTiac.objects.select_related("createur")
            .get_user_can_view(user)
            .with_fin_de_suivi(contact)
            .prefetch_related("etablissements")
        )

        return QuerySetSequence(evenement_simple_qs, investigation_qs)

    def get_queryset(self):
        raw_queryset = self.get_raw_queryset
        for idx, queryset in enumerate(raw_queryset._querysets):
            raw_queryset._querysets[idx] = self.apply_ordering(queryset)

        self.filter = TiacFilter(self.request.GET, queryset=raw_queryset)
        return self.filter.qs
