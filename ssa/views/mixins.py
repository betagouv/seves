from core.mixins import WithOrderingMixin
from ssa.filters import EvenementProduitFilter
from ssa.models import EvenementProduit


class WithFilteredListMixin(WithOrderingMixin):
    def get_ordering_fields(self):
        return {
            "numero_evenement": ("numero_annee", "numero_evenement"),
            "creation": "date_creation",
            "createur": "createur__libelle",
            "etat": "etat",
            "liens": "nb_liens_libre",
        }

    def get_default_order_by(self):
        return "numero_evenement"

    def get_queryset(self):
        user = self.request.user
        contact = user.agent.structure.contact_set.get()
        queryset = (
            EvenementProduit.objects.select_related("createur")
            .get_user_can_view(user)
            .with_fin_de_suivi(contact)
            .with_nb_liens_libres()
        )
        queryset = self.apply_ordering(queryset)
        self.filter = EvenementProduitFilter(self.request.GET, queryset=queryset)
        return self.filter.qs
