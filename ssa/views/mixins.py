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

    def get_nb_objects(self, user):
        count_1 = EvenementProduitReadOnly.objects.all().get_user_can_view(user).count()
        count_2 = EvenementInvestigationCasHumain.objects.all().get_user_can_view(user).count()
        return count_1 + count_2

    def get_raw_queryset(self, enable_pagination=True):
        user = self.request.user

        if hasattr(self, "paginate_by") and enable_pagination:
            ep_light_qs = EvenementProduitReadOnly.objects.all().get_user_can_view(user).optimized_for_list()
            ich_light_qs = EvenementInvestigationCasHumain.objects.all().get_user_can_view(user).optimized_for_list()
            return QuerySetSequence(ep_light_qs, ich_light_qs, model=EvenementProduit)

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
        self.nb_filtered_objects = EvenementFilter(
            self.request.GET, queryset=self.get_raw_queryset(enable_pagination=False)
        ).qs.count()
        return self.filter.qs


class EvenementProduitValuesMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorie_produit_data"] = json.dumps(CategorieProduit.build_options())
        context["categorie_danger"] = json.dumps(CategorieDanger.build_options(sorted_results=True))
        context["danger_plus_courant"] = EvenementProduit.danger_plus_courants()
        return context
