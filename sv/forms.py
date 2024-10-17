from core.forms import DSFRForm, WithNextUrlMixin

from django.contrib.contenttypes.models import ContentType
from core.fields import MultiModelChoiceField
from django import forms
from django.forms.models import inlineformset_factory
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.utils.translation import ngettext
from django.forms import BaseInlineFormSet


from core.models import LienLibre
from sv.models import FicheDetection
from core.models import Visibilite
from core.fields import DSFRRadioButton, DSFRCheckboxInput
from sv.models import FicheZoneDelimitee, ZoneInfestee


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


class FicheDetectionVisibiliteUpdateForm(DSFRForm, forms.ModelForm):
    class Meta:
        model = FicheDetection
        fields = ["visibilite"]
        widgets = {
            "visibilite": DSFRRadioButton(
                attrs={"hint_text": {choice.value: choice.label.capitalize() for choice in Visibilite}}
            ),
        }
        labels = {
            "visibilite": "",
        }

    def __init__(self, *args, **kwargs):
        obj = kwargs.pop("obj", None)
        super().__init__(*args, **kwargs)
        fiche_detection = obj or self.instance

        local = (Visibilite.LOCAL, Visibilite.LOCAL.capitalize())
        national = (Visibilite.NATIONAL, Visibilite.NATIONAL.capitalize())
        match fiche_detection.visibilite:
            case Visibilite.BROUILLON:
                choices = [local]
            case Visibilite.LOCAL | Visibilite.NATIONAL:
                choices = [local, national]
        self.fields["visibilite"].choices = choices

        self.fields["visibilite"].initial = fiche_detection.visibilite


class RattachementDetectionForm(DSFRForm, forms.Form):
    rattachement = forms.ChoiceField(
        choices=[
            ("hors_zone_infestee", "Détections hors zone infestée"),
            ("zone_infestee", "Zone infestée"),
        ],
        widget=DSFRRadioButton,
        label="Où souhaitez-vous rattacher la détection ?",
        initial="hors_zone_infestee",
    )


class FicheZoneDelimiteeForm(DSFRForm, forms.ModelForm):
    date_creation = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"disabled": "disabled", "value": now().strftime("%d/%m/%Y")}),
        required=False,
        label="Date de création",
    )
    unite_rayon_zone_tampon = forms.ChoiceField(
        choices=[(choice.value, choice.value) for choice in FicheZoneDelimitee.UnitesRayon],
        widget=DSFRRadioButton(attrs={"layout": "inline"}),
        initial=FicheZoneDelimitee.UnitesRayon.KILOMETRE,
    )
    unite_surface_tampon_totale = forms.ChoiceField(
        choices=[(choice.value, choice.value) for choice in FicheZoneDelimitee.UnitesSurfaceTamponTolale],
        widget=DSFRRadioButton(attrs={"layout": "inline"}),
        initial=FicheZoneDelimitee.UnitesSurfaceTamponTolale.METRE_CARRE,
    )
    detections_hors_zone = forms.ModelMultipleChoiceField(
        queryset=FicheDetection.objects.none(),
        widget=forms.SelectMultiple,
        required=False,
        label="Rattacher des détections",
    )

    class Meta:
        model = FicheZoneDelimitee
        fields = [
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
            "is_zone_tampon_toute_commune": DSFRCheckboxInput,
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        if self.user is None:
            raise ValueError("L'utilisateur doit être passé en paramètre.")
        self.detections_zones_infestees_formset = kwargs.pop("detections_zones_infestees_formset", None)
        hors_zone_infestee_detection = kwargs.pop("hors_zone_infestee_detection", None)
        super().__init__(*args, **kwargs)
        self.label_suffix = ""

        if hors_zone_infestee_detection:
            self.fields["detections_hors_zone"].queryset = (
                FicheDetection.objects.all()
                .get_all_not_in_fiche_zone_delimitee()
                .filter(organisme_nuisible=hors_zone_infestee_detection.organisme_nuisible)
            )
            self.fields["detections_hors_zone"].initial = [hors_zone_infestee_detection]

        is_zone_tampon_toute_commune_field = self.fields["is_zone_tampon_toute_commune"]
        label = self._meta.model._meta.get_field("is_zone_tampon_toute_commune").verbose_name
        is_zone_tampon_toute_commune_field.widget = DSFRCheckboxInput(label=label)

        if self.instance.pk:
            self.fields["detections_hors_zone"].initial = FicheDetection.objects.filter(
                hors_zone_infestee=self.instance, zone_infestee__isnull=True
            )

    def clean(self):
        if duplicate_fiches_detection := self._has_duplicate_detections():
            fiches = ", ".join(str(fiche) for fiche in duplicate_fiches_detection)
            message = ngettext(
                f"La fiche détection {fiches} ne peut pas être sélectionnée à la fois dans les zones infestées et dans hors zone infestée.",
                f"Les fiches détection {fiches} ne peuvent pas être sélectionnées à la fois dans les zones infestées et dans hors zone infestée.",
                len(duplicate_fiches_detection),
            )
            raise ValidationError(message)
        return super().clean()

    def _has_duplicate_detections(self):
        """Renvoie une liste d'id de fiches détection contenues à la fois dans les zones infestées et hors zone infestée."""
        detections_hors_zone = set(self.cleaned_data["detections_hors_zone"])
        duplicate_fiches_detection = detections_hors_zone.intersection(self.detections_zones_infestees_formset)
        return sorted([d.numero for d in duplicate_fiches_detection], key=lambda x: (x.annee, x.numero))

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.createur = self.user.agent.structure
        if commit:
            instance.save()
            self.save_detections_hors_zone(instance)
        return instance

    def save_detections_hors_zone(self, instance):
        detections_from_form = set(self.cleaned_data.get("detections_hors_zone", []))
        detections_from_db = set(FicheDetection.objects.filter(hors_zone_infestee=instance))

        detections_a_ajouter = detections_from_form - detections_from_db
        for detection in detections_a_ajouter:
            detection.hors_zone_infestee = instance
            detection.zone_infestee = None
            detection.save()

        detections_a_retirer = detections_from_db - detections_from_form
        for detection in detections_a_retirer:
            detection.hors_zone_infestee = None
            detection.save()


class ZoneInfesteeForm(DSFRForm, forms.ModelForm):
    unite_surface_infestee_totale = forms.ChoiceField(
        choices=[(choice.value, choice.value) for choice in ZoneInfestee.UnitesSurfaceInfesteeTotale],
        widget=DSFRRadioButton(attrs={"layout": "inline"}),
        initial=ZoneInfestee.UnitesSurfaceInfesteeTotale.METRE_CARRE,
    )
    detections = forms.ModelMultipleChoiceField(
        queryset=FicheDetection.objects.all().get_all_not_in_fiche_zone_delimitee(),
        widget=forms.SelectMultiple,
        required=False,
        label="Rattacher des détections",
    )

    class Meta:
        model = ZoneInfestee
        exclude = ["fiche_zone_delimitee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        if self.instance.pk:
            self.fields["detections"].initial = self.instance.fichedetection_set.all()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_detections(instance)
        return instance

    def save_detections(self, instance):
        detections_from_form = set(self.cleaned_data.get("detections", []))
        detections_from_db = set(instance.fichedetection_set.all())

        detections_a_ajouter = detections_from_form - detections_from_db
        for detection in detections_a_ajouter:
            detection.zone_infestee = instance
            detection.hors_zone_infestee = None
            detection.save()

        detections_a_retirer = detections_from_db - detections_from_form
        for detection in detections_a_retirer:
            detection.zone_infestee = None
            detection.save()


class ZoneInfesteeFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        detection = kwargs.pop("detection", None)
        super().__init__(*args, **kwargs)
        if not self.instance.pk and self.forms and detection:
            self.forms[0].fields["detections"].initial = [detection]

    def clean(self):
        super().clean()

        all_detections = set()
        duplicate_detections = set()
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                if detections := form.cleaned_data.get("detections"):
                    for detection in detections:
                        if detection in all_detections:
                            duplicate_detections.add(detection)
                        all_detections.add(detection)

        if duplicate_detections:
            duplicate_list = ", ".join(str(d) for d in duplicate_detections)
            raise ValidationError(
                f"Les fiches détection suivantes sont dupliquées dans les zones infestées : {duplicate_list}."
            )


ZoneInfesteeFormSet = inlineformset_factory(
    FicheZoneDelimitee, ZoneInfestee, form=ZoneInfesteeForm, formset=ZoneInfesteeFormSet, extra=1, can_delete=False
)
