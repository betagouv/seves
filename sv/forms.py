from core.forms import DSFRForm, WithNextUrlMixin

from django.contrib.contenttypes.models import ContentType
from core.fields import MultiModelChoiceField
from django import forms
from django.forms.models import inlineformset_factory
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.utils.translation import ngettext
from django.forms import BaseInlineFormSet
from django.db.models import TextChoices


from core.models import LienLibre
from core.models import Visibilite
from core.fields import DSFRRadioButton, DSFRCheckboxInput
from sv.models import FicheZoneDelimitee, ZoneInfestee, OrganismeNuisible, StatutReglementaire, FicheDetection


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
            model_choices=[
                ("Fiche Detection", FicheDetection.objects.select_related("numero")),
                ("Fiche Zone Delimitee", FicheZoneDelimitee.objects.select_related("numero")),
            ],
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


class RattachementChoices(TextChoices):
    HORS_ZONE_INFESTEE = "hors_zone_infestee", "Hors zone infestée"
    ZONE_INFESTEE = "zone_infestee", "Zone infestée"


class RattachementDetectionForm(DSFRForm, forms.Form):
    rattachement = forms.ChoiceField(
        choices=RattachementChoices.choices,
        widget=DSFRRadioButton,
        label="Où souhaitez-vous rattacher la détection ?",
        initial=RattachementChoices.HORS_ZONE_INFESTEE,
    )


class FicheZoneDelimiteeForm(DSFRForm, forms.ModelForm):
    organisme_nuisible = forms.CharField(
        widget=forms.TextInput(attrs={"readonly": ""}),
        label="Organisme nuisible",
    )
    statut_reglementaire = forms.CharField(
        widget=forms.TextInput(attrs={"readonly": ""}),
        label="Statut réglementaire",
    )
    date_creation = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"disabled": "", "value": now().strftime("%d/%m/%Y")}),
        required=False,
        label="Date de création",
    )
    unite_rayon_zone_tampon = forms.ChoiceField(
        choices=[(choice.value, choice.value) for choice in FicheZoneDelimitee.UnitesRayon],
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        initial=FicheZoneDelimitee.UnitesRayon.KILOMETRE,
    )
    unite_surface_tampon_totale = forms.ChoiceField(
        choices=[(choice.value, choice.value) for choice in FicheZoneDelimitee.UnitesSurfaceTamponTolale],
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
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
        exclude = ["date_creation", "numero", "createur"]
        labels = {
            "statut_reglementaire": "Statut réglementaire",
            "caracteristiques_principales_zone_delimitee": "Caractéristiques",
        }
        widgets = {
            "createur": forms.HiddenInput,
            "vegetaux_infestes": forms.Textarea(attrs={"rows": 1}),
            "commentaire": forms.Textarea(attrs={"rows": 5}),
            "is_zone_tampon_toute_commune": DSFRCheckboxInput(
                label="La zone tampon s'étend à toute la ou les commune(s)"
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.detections_zones_infestees_formset = kwargs.pop("detections_zones_infestees_formset", None)

        super().__init__(*args, **kwargs)
        self.label_suffix = ""

        organisme_nuisible_libelle = self.data.get("organisme_nuisible") or self.initial.get("organisme_nuisible")
        self.fields["detections_hors_zone"].queryset = (
            FicheDetection.objects.all()
            .get_all_not_in_fiche_zone_delimitee()
            .filter(organisme_nuisible__libelle_court=organisme_nuisible_libelle)
        )
        if self.instance.pk:
            self.fields["detections_hors_zone"].initial = FicheDetection.objects.filter(
                hors_zone_infestee=self.instance, zone_infestee__isnull=True
            )

    def clean_organisme_nuisible(self):
        return OrganismeNuisible.objects.get(libelle_court=self.cleaned_data["organisme_nuisible"])

    def clean_statut_reglementaire(self):
        return StatutReglementaire.objects.get(libelle=self.cleaned_data["statut_reglementaire"])

    def clean(self):
        if duplicate_fiches_detection := self._get_duplicate_detections():
            fiches = ", ".join(str(fiche) for fiche in duplicate_fiches_detection)
            message = ngettext(
                f"La fiche détection {fiches} ne peut pas être sélectionnée à la fois dans les zones infestées et dans hors zone infestée.",
                f"Les fiches détection {fiches} ne peuvent pas être sélectionnées à la fois dans les zones infestées et dans hors zone infestée.",
                len(duplicate_fiches_detection),
            )
            raise ValidationError(message)
        return super().clean()

    def _get_duplicate_detections(self):
        """Renvoie une liste d'id de fiches détection contenues à la fois dans les zones infestées et hors zone infestée."""
        detections_hors_zone = set(self.cleaned_data.get("detections_hors_zone", []))
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
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        initial=ZoneInfestee.UnitesSurfaceInfesteeTotale.METRE_CARRE,
    )
    unite_rayon = forms.ChoiceField(
        choices=[(choice.value, choice.value) for choice in ZoneInfestee.UnitesRayon],
        widget=DSFRRadioButton(attrs={"class": "fr-fieldset__element--inline"}),
        initial=ZoneInfestee.UnitesRayon.KILOMETRE,
    )
    detections = forms.ModelMultipleChoiceField(
        queryset=FicheDetection.objects.none(),
        widget=forms.SelectMultiple,
        required=False,
        label="Rattacher des détections",
    )

    class Meta:
        model = ZoneInfestee
        exclude = ["fiche_zone_delimitee"]

    def __init__(self, *args, **kwargs):
        self.organisme_nuisible = kwargs.pop("organisme_nuisible", None)
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        if self.organisme_nuisible:
            self.fields["detections"].queryset = (
                FicheDetection.objects.all()
                .get_all_not_in_fiche_zone_delimitee()
                .filter(organisme_nuisible__libelle_court=self.organisme_nuisible)
            )
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
        organisme_nuisible = kwargs.pop("organisme_nuisible", None)
        detection = kwargs.pop("detection", None)
        self.organisme_nuisible = organisme_nuisible or args[0].get("organisme_nuisible")
        super().__init__(*args, **kwargs)
        if not self.instance.pk and self.forms and detection:
            self.forms[0].fields["detections"].initial = [detection]

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["organisme_nuisible"] = self.organisme_nuisible
        return kwargs

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
