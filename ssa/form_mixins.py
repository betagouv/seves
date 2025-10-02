from core.fields import MultiModelChoiceField
from core.form_mixins import WithFreeLinksMixin
from ssa.models import EvenementProduit
from tiac.models import EvenementSimple, InvestigationTiac


class WithEvenementProduitFreeLinksMixin(WithFreeLinksMixin):
    model_label = "Événement produit"

    def get_queryset(self, model, user, instance):
        queryset = (
            model.objects.all().order_by_numero().get_user_can_view(user).exclude(etat=EvenementProduit.Etat.BROUILLON)
        )
        if instance:
            queryset = queryset.exclude(id=instance.id)
        return queryset

    def _get_evenement_simple_queryset(self, user):
        return (
            EvenementSimple.objects.all()
            .order_by_numero()
            .get_user_can_view(user)
            .exclude(etat=EvenementSimple.Etat.BROUILLON)
        )

    def _get_investigation_tiac_queryset(self, user):
        return (
            InvestigationTiac.objects.all()
            .order_by_numero()
            .get_user_can_view(user)
            .exclude(etat=EvenementSimple.Etat.BROUILLON)
        )

    def _add_free_links(self, model):
        instance = getattr(self, "instance", None)
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=[
                (self.model_label, self.get_queryset(model, self.user, instance)),
                ("Enregistrement simple", self._get_evenement_simple_queryset(self.user)),
                ("Investigation de tiac", self._get_investigation_tiac_queryset(self.user)),
            ],
        )
