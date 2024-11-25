from django.core.exceptions import ValidationError

from core.fields import MultiModelChoiceField
from core.models import LienLibre
from sv.models import FicheDetection, FicheZoneDelimitee


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

    def _add_free_links(self, obj_type):
        qs_detection = FicheDetection.objects.all().order_by_numero_fiche().get_fiches_user_can_view(self.user)
        qs_detection = qs_detection.select_related("numero")
        qs_zone = FicheZoneDelimitee.objects.all().order_by_numero_fiche().get_fiches_user_can_view(self.user)
        qs_zone = qs_zone.select_related("numero")
        if self.instance:
            if obj_type == "zone":
                qs_zone = qs_zone.exclude(id=self.instance.id)
            elif obj_type == "detection":
                qs_detection = qs_detection.exclude(id=self.instance.id)
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=[
                ("Fiche Détection", qs_detection),
                ("Fiche zone délimitée", qs_zone),
            ],
        )

    def clean_free_link(self):
        if self.instance and self.instance in self.cleaned_data["free_link"]:
            raise ValidationError("Vous ne pouvez pas lier une fiche a elle-même.")
        return self.cleaned_data["free_link"]
