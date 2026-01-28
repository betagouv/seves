from collections import defaultdict

from django import forms
from django.core.exceptions import ValidationError
from django.forms import Script

from core.fields import MultiModelChoiceField
from core.models import LienLibre


def js_module(src, **attributes):
    attributes["type"] = "module"
    return Script(src, **attributes)


class DSFRForm(forms.Form):
    input_to_class = defaultdict(lambda: "fr-input")
    input_to_class["ClearableFileInput"] = "fr-upload"
    input_to_class["Select"] = "fr-select"
    input_to_class["SelectMultiple"] = "fr-select"
    input_to_class["SelectWithAttributeField"] = "fr-select"
    input_to_class["DSFRRadioButton"] = ""
    input_to_class["DSFRCheckboxSelectMultiple"] = ""
    manual_render_fields = []

    def get_context(self):
        context = super().get_context()
        context["manual_render_fields"] = self.manual_render_fields
        return context

    def as_dsfr_div(self):
        return self.render("core/_dsfr_div.html")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        for field in self.fields:
            widget = self.fields[field].widget
            class_to_add = self.input_to_class[type(widget).__name__]
            widget.attrs["class"] = widget.attrs.get("class", "") + " " + class_to_add


class WithFreeLinksMixin:
    model_label = "Unknown"

    def save_free_links(self, instance):
        links_ids_to_keep = []
        for obj in self.cleaned_data["free_link"]:
            link = LienLibre.objects.for_both_objects(obj, instance)

            if link:
                links_ids_to_keep.append(link.id)
            else:
                link = LienLibre(related_object_1=instance, related_object_2=obj)
                link._user = self.user
                link.save()
                links_ids_to_keep.append(link.id)

        links_to_delete = LienLibre.objects.for_object(instance).exclude(id__in=links_ids_to_keep)
        for link in links_to_delete:
            link._user = self.user
            link.delete()

    def get_queryset(self, model, user, instance):
        raise NotImplementedError

    def _add_free_links(self, model):
        instance = getattr(self, "instance", None)
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=[
                (self.model_label, self.get_queryset(model, self.user, instance)),
            ],
        )

    def clean_free_link(self):
        if self.instance and self.instance in self.cleaned_data["free_link"]:
            raise ValidationError("Vous ne pouvez pas lier un objet a lui-même.")
        return self.cleaned_data["free_link"]


class WithLatestVersionLocking(forms.Form):
    latest_version = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.latest_version = kwargs.pop("latest_version", 0)
        super().__init__(*args, **kwargs)
        self.fields["latest_version"].widget.attrs["value"] = self.latest_version

    def clean(self):
        super().clean()
        if self.cleaned_data.get("latest_version") and self.latest_version != self.cleaned_data["latest_version"]:
            raise ValidationError(
                "Les modifications n'ont pas pu être enregistrées car un autre utilisateur à modifié la fiche.",
                code="blocking_error",
            )
