from django.db.models import Case, F, When

from core.mixins import WithOrderingMixin
from sa.filters import EvenementAnimalFilter
from sa.models import EvenementAnimal


class WithFilteredListMixin(WithOrderingMixin):
    def get_ordering_fields(self):
        return {
            "numero_evenement": ("numero_annee", "numero_evenement"),
            "maladie": "maladie__name",
            "departement": "departement__numero",
            "commune": "commune",
            "statut_evenement": "statut_evenement",
            "creation": "date_creation",
            "etat": "etat",
        }

    def get_default_order_by(self):
        return "creation"

    def get_raw_queryset(self):
        user = self.request.user
        contact = self.request.user.agent.structure.contact_set.get()
        queryset = EvenementAnimal.objects.all().get_user_can_view(user).with_fin_de_suivi(contact).optimized_for_list()
        queryset = queryset.annotate(
            displayed_detenteur=Case(
                When(numero_identifiant_etablissement__isnull=False, then=F("numero_identifiant_etablissement")),
                default=F("nom_particulier"),
            )
        )
        return queryset

    def get_queryset(self):
        queryset = self.apply_ordering(self.get_raw_queryset())
        self.filter = EvenementAnimalFilter(self.request.GET, queryset=queryset)
        return self.filter.qs
