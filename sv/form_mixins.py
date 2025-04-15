from django import forms
from django.core.exceptions import ValidationError

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


class WithLatestVersionLocking(forms.Form):
    latest_version = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.latest_version = kwargs.pop("latest_version")
        super().__init__(*args, **kwargs)
        self.fields["latest_version"].widget.attrs["value"] = self.latest_version

    def clean(self):
        super().clean()
        if self.cleaned_data.get("latest_version") and self.latest_version != self.cleaned_data["latest_version"]:
            raise ValidationError(
                "Les modifications n'ont pas pu être enregistrées car un autre utilisateur à modifié la fiche.",
                code="blocking_error",
            )
