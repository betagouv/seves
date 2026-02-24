import json

from queryset_sequence import QuerySetSequence

from core.mixins import WithOrderingMixin
from ssa.constants import CategorieDanger, CategorieProduit
from ssa.filters import EvenementFilter
from ssa.models import EvenementInvestigationCasHumain, EvenementProduit
from ssa.models.evenement_produit import EvenementProduitReadOnly


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
        queryset = self.apply_ordering(self.get_raw_queryset())
        self.filter = EvenementFilter(self.request.GET, queryset=queryset)
        return self.filter.qs


class EvenementProduitValuesMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorie_produit_data"] = json.dumps(CategorieProduit.build_options())
        context["categorie_danger"] = json.dumps(CategorieDanger.build_options(sorted_results=True))
        context["danger_plus_courant"] = EvenementProduit.danger_plus_courants()
        return context
