from core.forms import DSFRForm, WithNextUrlMixin

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from core.fields import MultiModelChoiceField
from django import forms
from django.forms.models import inlineformset_factory

from core.models import LienLibre
from sv.models import FicheDetection, FicheZoneDelimitee, ZoneInfestee, HorsZoneInfestee


class FreeLinkForm(DSFRForm, WithNextUrlMixin, forms.ModelForm):
    object_id_1 = forms.IntegerField(widget=forms.HiddenInput())
    content_type_1 = forms.ModelChoiceField(widget=forms.HiddenInput(), queryset=ContentType.objects.all())

    class Meta:
        fields = ["object_id_1", "content_type_1"]
        model = LienLibre

    def __init__(self, *args, **kwargs):
        object_id_1 = kwargs.pop("object_id_1", None)
        content_type_1 = kwargs.pop("content_type_1", None)
        next = kwargs.pop("next", None)
        super().__init__(*args, **kwargs)
        self.fields["object_choice"] = MultiModelChoiceField(
            label="Sélectioner un objet",
            model_choices=[("FicheDetection", FicheDetection.objects.select_related("numero"))],
        )
        self.add_next_field(next)
        self.fields["object_id_1"].initial = object_id_1
        self.fields["content_type_1"].initial = content_type_1

    def clean(self):
        super().clean()
        obj = self.cleaned_data["object_choice"]
        self.instance.content_type_2 = ContentType.objects.get_for_model(obj)
        self.instance.object_id_2 = obj.id


class FicheZoneDelimiteeForm(DSFRForm, forms.ModelForm):
    detections_hors_zone = forms.ModelMultipleChoiceField(
        queryset=FicheDetection.objects.get_all_not_in_fiche_zone_delimitee(),
        widget=forms.SelectMultiple,
        required=False,
        label="Détections hors zone infestée",
    )

    class Meta:
        model = FicheZoneDelimitee
        fields = [
            "createur",
            "caracteristiques_principales_zone_delimitee",
            "vegetaux_infestes",
            "commentaire",
            "rayon_zone_tampon",
            "unite_rayon_zone_tampon",
            "surface_tampon_totale",
            "unite_surface_tampon_totale",
            "is_zone_tampon_toute_commune",
        ]
        labels = {
            "caracteristiques_principales_zone_delimitee": "Caractéristiques",
        }
        widgets = {
            "createur": forms.HiddenInput(),
            "vegetaux_infestes": forms.Textarea(attrs={"rows": 1}),
            "commentaire": forms.Textarea(attrs={"rows": 5}),
            "unite_rayon_zone_tampon": forms.RadioSelect(),
            "unite_surface_tampon_totale": forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        createur = kwargs.pop("createur", None)
        super().__init__(*args, **kwargs)
        if createur:
            self.fields["createur"].initial = createur
        # Affichage version courte des choix pour les unités (m², ha, km, etc.)
        self.fields["unite_rayon_zone_tampon"].widget.choices = [
            (choice.value, choice.value) for choice in FicheZoneDelimitee.UnitesRayon
        ]
        self.fields["unite_surface_tampon_totale"].widget.choices = [
            (choice.value, choice.value) for choice in FicheZoneDelimitee.UnitesSurfaceTamponTolale
        ]
        if self.instance.pk and self.instance.detections_hors_zone_infestee:
            self.fields[
                "detections_hors_zone"
            ].initial = self.instance.detections_hors_zone_infestee.fiches_detection.all()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not hasattr(instance, "detections_hors_zone_infestee"):
            instance.detections_hors_zone_infestee = HorsZoneInfestee.objects.create()
        if commit:
            instance.save()
            self.save_detections_hors_zone(instance)
        return instance

    def save_detections_hors_zone(self, instance):
        detections = self.cleaned_data.get("detections_hors_zone")
        print(detections)
        hors_zone = instance.detections_hors_zone_infestee

        # Mettre à jour les détections qui ne sont plus hors zone
        FicheDetection.objects.filter(hors_zone_infestee=hors_zone).exclude(id__in=[d.id for d in detections]).update(
            hors_zone_infestee=None
        )

        # Mettre à jour les nouvelles détections qui sont hors zone
        detections_to_update = detections.filter(~Q(hors_zone_infestee=hors_zone))
        detections_to_update.update(hors_zone_infestee=hors_zone, zone_infestee=None)


class ZoneInfesteeForm(DSFRForm, forms.ModelForm):
    detections = forms.ModelMultipleChoiceField(
        queryset=FicheDetection.objects.get_all_not_in_fiche_zone_delimitee(),
        widget=forms.SelectMultiple,
        required=False,
        label="Détections dans la zone infestée",
    )

    class Meta:
        model = ZoneInfestee
        exclude = ["fiche_zone_delimitee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["detections"].initial = self.instance.fiches_detection.all()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_detections(instance)
        return instance

    def save_detections(self, instance):
        instance.fiches_detection.set(self.cleaned_data["detections"])


ZoneInfesteeFormSet = inlineformset_factory(
    FicheZoneDelimitee, ZoneInfestee, form=ZoneInfesteeForm, extra=1, can_delete=False
)
