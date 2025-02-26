from django.core.exceptions import ValidationError

from core.fields import MultiModelChoiceField
from core.models import LienLibre
from sv.models import Evenement
from django import forms


class WithDataRequiredConversionMixin:
    def _convert_required_to_data_required(self):
        for field in self:
            if field.field.required:
                field.field.widget.attrs["data-required"] = "true"
                field.field.widget.attrs.pop("required", None)
                field.field.required = False


class WithFreeLinksMixin:
    def save_free_links(self, instance):
        links_ids_to_keep = []
        for obj in self.cleaned_data["free_link"]:
            link = LienLibre.objects.for_both_objects(obj, instance)

            if link:
                links_ids_to_keep.append(link.id)
            else:
                link = LienLibre.objects.create(related_object_1=instance, related_object_2=obj)
                links_ids_to_keep.append(link.id)

        links_to_delete = LienLibre.objects.for_object(instance).exclude(id__in=links_ids_to_keep)
        links_to_delete.delete()

    def _add_free_links(self, model):
        queryset = (
            model.objects.all()
            .order_by_numero()
            .get_user_can_view(self.user)
            .exclude(id=self.instance.id)
            .exclude(etat=Evenement.Etat.BROUILLON)
        )
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=[
                ("Événement", queryset),
            ],
        )

    def clean_free_link(self):
        if self.instance and self.instance in self.cleaned_data["free_link"]:
            raise ValidationError("Vous ne pouvez pas lier un objet a lui-même.")
        return self.cleaned_data["free_link"]


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
