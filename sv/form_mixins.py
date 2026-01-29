from core.form_mixins import WithFreeLinksMixin
from sv.models import Evenement


class WithDataRequiredConversionMixin:
    def _convert_required_to_data_required(self):
        for field in self:
            if field.field.required:
                field.field.widget.attrs["data-required"] = "true"
                field.field.widget.attrs.pop("required", None)
                field.field.required = False


class WithEvenementFreeLinksMixin(WithFreeLinksMixin):
    model_label = "Événement"

    def get_queryset(self, model, user, instance):
        return (
            model.objects.all()
            .order_by_numero()
            .get_user_can_view(user)
            .exclude(id=instance.id)
            .exclude(etat=Evenement.Etat.BROUILLON)
        )
