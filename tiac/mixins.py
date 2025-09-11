from core.mixins import WithOrderingMixin
from tiac.filters import EvenementSimpleFilter
from tiac.models import EvenementSimple


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

    def get_raw_queryset(self):
        user = self.request.user
        contact = user.agent.structure.contact_set.get()
        return EvenementSimple.objects.select_related("createur").get_user_can_view(user).with_fin_de_suivi(contact)

    def get_queryset(self):
        queryset = self.apply_ordering(self.get_raw_queryset())
        self.filter = EvenementSimpleFilter(self.request.GET, queryset=queryset)
        return self.filter.qs
