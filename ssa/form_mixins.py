from core.form_mixins import WithFreeLinksMixin
from ssa.models import EvenementProduit


class WithEvenementProduitFreeLinksMixin(WithFreeLinksMixin):
    model_label = "Événement produit"

    def get_queryset(self, model, user, instance):
        queryset = (
            model.objects.all().order_by_numero().get_user_can_view(user).exclude(etat=EvenementProduit.Etat.BROUILLON)
        )
        if instance:
            queryset = queryset.exclude(id=instance.id)
        return queryset
