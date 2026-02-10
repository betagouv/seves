from core.fields import MultiModelChoiceField
from core.form_mixins import WithFreeLinksMixin
from ssa.models import EvenementProduit
from tiac.models import EvenementSimple, InvestigationTiac


class WithFreeLinksQuerysetsMixin:
    def get_queryset(self, model, user, instance):
        queryset = (
            model.objects.all().order_by_numero().get_user_can_view(user).exclude(etat=EvenementProduit.Etat.BROUILLON)
        )
        if instance:
            queryset = queryset.exclude(id=instance.id)
        return queryset

    def _get_cas_humain_queryset(self, user):
        from core.mixins import WithEtatMixin
        from ssa.models import EvenementInvestigationCasHumain

        return (
            EvenementInvestigationCasHumain.objects.all()
            .order_by_numero()
            .get_user_can_view(user)
            .exclude(etat=WithEtatMixin.Etat.BROUILLON)
        )

    def _get_evenement_simple_queryset(self, user):
        from core.mixins import WithEtatMixin

        return (
            EvenementSimple.objects.all()
            .order_by_numero()
            .get_user_can_view(user)
            .exclude(etat=WithEtatMixin.Etat.BROUILLON)
        )

    def _get_investigation_tiac_queryset(self, user):
        from core.mixins import WithEtatMixin

        return (
            InvestigationTiac.objects.all()
            .order_by_numero()
            .get_user_can_view(user)
            .exclude(etat=WithEtatMixin.Etat.BROUILLON)
        )


class WithEvenementProduitFreeLinksMixin(WithFreeLinksQuerysetsMixin, WithFreeLinksMixin):
    model_label = "Événement produit"

    def _add_free_links(self, model):
        instance = getattr(self, "instance", None)
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=[
                (self.model_label, self.get_queryset(model, self.user, instance)),
                ("Investigation de cas humain", self._get_cas_humain_queryset(self.user)),
                ("Enregistrement simple", self._get_evenement_simple_queryset(self.user)),
                ("Investigation de tiac", self._get_investigation_tiac_queryset(self.user)),
            ],
        )
