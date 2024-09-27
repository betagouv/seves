from core.forms import DSFRForm, WithNextUrlMixin

from django.contrib.contenttypes.models import ContentType

from core.fields import MultiModelChoiceField
from django import forms
from django.forms.models import inlineformset_factory

from core.models import LienLibre
from sv.models import FicheDetection, FicheZoneDelimitee, ZoneInfestee


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
        if self.instance.pk:
            self.fields["detections_hors_zone"].initial = FicheDetection.objects.filter(
                hors_zone_infestee=self.instance, zone_infestee__isnull=True
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_detections_hors_zone(instance)
        return instance

    def save_detections_hors_zone(self, instance):
        nouvelles_detections = set(self.cleaned_data.get("detections_hors_zone", []))
        anciennes_detections = set(FicheDetection.objects.filter(hors_zone_infestee=instance))

        # Détections à ajouter
        detections_a_ajouter = nouvelles_detections - anciennes_detections
        if detections_a_ajouter:
            FicheDetection.objects.filter(id__in=[d.id for d in detections_a_ajouter]).update(
                hors_zone_infestee=instance, zone_infestee=None
            )

        # Détections à retirer
        detections_a_retirer = anciennes_detections - nouvelles_detections
        if detections_a_retirer:
            FicheDetection.objects.filter(id__in=[d.id for d in detections_a_retirer]).update(hors_zone_infestee=None)


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
        # instance.fiches_detection.set(self.cleaned_data["detections"])
        nouvelles_detections = set(self.cleaned_data.get("detections", []))
        anciennes_detections = set(instance.fiches_detection.all())

        # Détections à ajouter
        detections_a_ajouter = nouvelles_detections - anciennes_detections
        if detections_a_ajouter:
            FicheDetection.objects.filter(id__in=[d.id for d in detections_a_ajouter]).update(
                zone_infestee=instance, hors_zone_infestee=None
            )

        # Détections à retirer
        detections_a_retirer = anciennes_detections - nouvelles_detections
        if detections_a_retirer:
            FicheDetection.objects.filter(id__in=[d.id for d in detections_a_retirer]).update(zone_infestee=None)


ZoneInfesteeFormSet = inlineformset_factory(
    FicheZoneDelimitee, ZoneInfestee, form=ZoneInfesteeForm, extra=1, can_delete=False
)
