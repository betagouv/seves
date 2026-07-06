from queryset_sequence import QuerySetSequence
import waffle

from core.mixins import WithOrderingMixin
from ssa.filters import EvenementFilter, EvenementFilterTreeselect
from ssa.models import EvenementInvestigationCasHumain, EvenementProduit
from ssa.models.evenement_produit import EvenementProduitReadOnly


class WithFilteredListMixin(WithOrderingMixin):
    def get_ordering_fields(self):
        return {
            "numero_evenement": ("numero_annee", "numero_evenement"),
            "last_update": "last_updated",
            "publication": "date_publication",
            "createur": "createur__libelle",
            "etat": "etat",
        }

    def get_default_order_by(self):
        return "numero_evenement"

    def get_raw_queryset(self):
        user = self.request.user
        contact = user.agent.structure.contact_set.get()

        evenement_produit_qs = (
            EvenementProduitReadOnly.objects.select_related("createur")
            .get_user_can_view(user)
            .with_fin_de_suivi(contact)
            .optimized_for_list()
        )

        ich_qs = (
            EvenementInvestigationCasHumain.objects.select_related("createur")
            .get_user_can_view(user)
            .with_fin_de_suivi(contact)
            .optimized_for_list()
        )

        return QuerySetSequence(evenement_produit_qs, ich_qs, model=EvenementProduit)

    def get_queryset(self):
        filter_klass = (
            EvenementFilterTreeselect if waffle.flag_is_active(self.request, "new_treeselect") else EvenementFilter
        )
        queryset = self.apply_ordering(self.get_raw_queryset())
        self.filter = filter_klass(self.request.GET, queryset=queryset)
        return self.filter.qs
