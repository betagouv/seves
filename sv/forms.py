import datetime

from core.forms import DSFRForm, VisibiliteUpdateBaseForm

from django import forms
from django.forms.models import inlineformset_factory
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.utils.translation import ngettext
from django.forms import BaseInlineFormSet
from django.db.models import TextChoices

from core.fields import DSFRRadioButton
from sv.form_mixins import WithDataRequiredConversionMixin, WithFreeLinksMixin
from sv.models import (
    FicheZoneDelimitee,
    ZoneInfestee,
    OrganismeNuisible,
    StatutReglementaire,
    FicheDetection,
    Lieu,
    Prelevement,
    Departement,
    EspeceEchantillon,
    LaboratoireAgree,
    LaboratoireConfirmationOfficielle,
    StructurePreleveur,
)


class FicheDetectionVisibiliteUpdateForm(VisibiliteUpdateBaseForm, forms.ModelForm):
    class Meta:
        model = FicheDetection
        fields = ["visibilite"]


class FicheZoneDelimiteeVisibiliteUpdateForm(VisibiliteUpdateBaseForm, forms.ModelForm):
    class Meta:
        model = FicheZoneDelimitee
        fields = ["visibilite"]


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


class LieuForm(DSFRForm, WithDataRequiredConversionMixin, forms.ModelForm):
    # TODO add id here and change saving logic
    nom = forms.CharField(widget=forms.TextInput(), required=True)
    commune = forms.CharField(widget=forms.HiddenInput(), required=False)
    code_insee = forms.CharField(widget=forms.HiddenInput(), required=False)
    departement = forms.ModelChoiceField(
        queryset=Departement.objects.all(),
        to_field_name="numero",
        required=False,
        widget=forms.Select(attrs={"class": "fr-hidden"}),
    )
    wgs84_longitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "style": "flex: 0.55; margin-right: .5rem;",
                "placeholder": "Longitude",
            }
        ),
    )
    wgs84_latitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "style": "flex: 0.55; margin-top: .5rem;",
                "placeholder": "Latitude",
            }
        ),
    )

    class Meta:
        model = Lieu
        exclude = []
        labels = {"is_etablissement": "Il s'agit d'un établissement"}

    def clean_departement(self):
        if self.cleaned_data["departement"] == "":
            return None
        return self.cleaned_data["departement"]

    def __init__(self, *args, **kwargs):
        convert_required_to_data_required = kwargs.pop("convert_required_to_data_required", False)
        super().__init__(*args, **kwargs)

        if convert_required_to_data_required:
            self._convert_required_to_data_required()

    def clean(self):
        super().clean()
        if not self.cleaned_data["is_etablissement"]:
            for field in Lieu.ETABLISSEMENT_FIELDS:
                self.cleaned_data.pop(field)


class CustomLieuFormSet(BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if hasattr(self, "custom_kwargs"):
            kwargs.update(self.custom_kwargs)
        return kwargs


LieuFormSet = inlineformset_factory(
    FicheDetection, Lieu, form=LieuForm, formset=CustomLieuFormSet, extra=10, can_delete=True
)


class PrelevementForm(DSFRForm, WithDataRequiredConversionMixin, forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    resultat = forms.ChoiceField(
        required=True,
        choices=Prelevement.Resultat.choices,
        widget=DSFRRadioButton(attrs={"required": "true"}),
    )
    lieu = forms.ModelChoiceField(
        queryset=Lieu.objects.none(),
        to_field_name="nom",
        required=True,
        empty_label=None,
    )
    espece_echantillon = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Prelevement
        exclude = []
        labels = {"date_prelevement": "Date prélèvement"}

    def _change_queryset_if_inactive_value(self, model, field_name):
        actual_ids = Prelevement.objects.filter(lieu__fiche_detection__pk=self.instance.pk)
        actual_ids = actual_ids.values_list(field_name + "_id", flat=True)
        inactive_ids = model._base_manager.filter(is_active=False).values_list("id", flat=True)
        if any([pk in inactive_ids for pk in actual_ids if pk]):
            self.fields[field_name].queryset = model._base_manager.order_by("nom")

    def __init__(self, *args, **kwargs):
        convert_required_to_data_required = kwargs.pop("convert_required_to_data_required", False)
        super().__init__(*args, **kwargs)
        self.fields["structure_preleveur"].required = "required"

        if self.instance:
            self._change_queryset_if_inactive_value(LaboratoireAgree, "laboratoire_agree")
            self._change_queryset_if_inactive_value(
                LaboratoireConfirmationOfficielle, "laboratoire_confirmation_officielle"
            )
            self._change_queryset_if_inactive_value(StructurePreleveur, "structure_preleveur")

        if convert_required_to_data_required:
            self._convert_required_to_data_required()

    def clean_espece_echantillon(self):
        if self.cleaned_data["espece_echantillon"]:
            return EspeceEchantillon.objects.get(pk=self.cleaned_data["espece_echantillon"])

    def clean(self):
        super().clean()
        if not self.cleaned_data["is_officiel"]:
            for field in Prelevement.OFFICIEL_FIELDS:
                self.cleaned_data.pop(field)


class FicheDetectionForm(DSFRForm, WithFreeLinksMixin, forms.ModelForm):
    vegetaux_infestes = forms.CharField(
        label="Végétaux infestés", max_length=500, required=False, widget=forms.Textarea(attrs={"rows": ""})
    )
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={"rows": ""}),
        required=False,
    )
    mesures_conservatoires_immediates = forms.CharField(
        widget=forms.Textarea(attrs={"rows": ""}),
        required=False,
        label="Mesures conservatoires immédiates",
    )
    mesures_consignation = forms.CharField(
        widget=forms.Textarea(attrs={"rows": ""}), required=False, label="Mesures de consignation"
    )
    mesures_phytosanitaires = forms.CharField(
        widget=forms.Textarea(attrs={"rows": ""}),
        required=False,
    )
    mesures_surveillance_specifique = forms.CharField(
        widget=forms.Textarea(attrs={"rows": ""}), required=False, label="Mesures de surveillance spécifique"
    )
    date_premier_signalement = forms.DateField(
        label="Date 1er signalement",
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"max": datetime.date.today(), "type": "date"}),
    )

    class Meta:
        model = FicheDetection
        exclude = ["numero", "createur", "etat"]
        fields = [
            "statut_evenement",
            "numero_europhyt",
            "numero_rasff",
            "organisme_nuisible",
            "statut_reglementaire",
            "contexte",
            "date_premier_signalement",
            "vegetaux_infestes",
            "commentaire",
            "mesures_conservatoires_immediates",
            "mesures_consignation",
            "mesures_phytosanitaires",
            "mesures_surveillance_specifique",
        ]
        labels = {
            "statut_evenement": "Statut évènement",
            "organisme_nuisible": "Organisme nuisible",
            "statut_reglementaire": "Statut réglementaire",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")

        super().__init__(*args, **kwargs)

        if not self.user.agent.structure.is_ac:
            self.fields.pop("numero_europhyt")
            self.fields.pop("numero_rasff")

        self._add_free_links(obj_type="detection")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.createur = self.user.agent.structure
        if commit:
            instance.save()
            self.save_free_links(instance)
        return instance


class FicheZoneDelimiteeForm(DSFRForm, WithFreeLinksMixin, forms.ModelForm):
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
        exclude = ["date_creation", "numero", "createur", "etat"]
        labels = {
            "statut_reglementaire": "Statut réglementaire",
        }
        widgets = {
            "createur": forms.HiddenInput,
            "vegetaux_infestes": forms.Textarea(attrs={"rows": 1}),
            "commentaire": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.detections_zones_infestees_formset = kwargs.pop("detections_zones_infestees_formset", None)

        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields.pop("visibilite")

        self._add_free_links(obj_type="zone")

        organisme_nuisible_libelle = self.data.get("organisme_nuisible") or self.initial.get("organisme_nuisible")
        self.fields["detections_hors_zone"].queryset = (
            FicheDetection.objects.all()
            .get_all_not_in_fiche_zone_delimitee(
                organisme_nuisible_libelle, self.instance if self.instance.pk else None
            )
            .exclude_brouillon()
            .order_by_numero_fiche()
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
            self.save_free_links(instance)
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
        labels = {
            "caracteristique_principale": "Caractéristique",
        }

    def __init__(self, *args, **kwargs):
        organisme_nuisible_libelle = kwargs.pop("organisme_nuisible_libelle", None)
        fiche_zone_delimitee = kwargs.pop("fiche_zone_delimitee", None)

        super().__init__(*args, **kwargs)

        fiche_zone_delimitee = (
            self.instance.fiche_zone_delimitee
            if not fiche_zone_delimitee and self.instance.fiche_zone_delimitee_id
            else fiche_zone_delimitee
        )

        self.fields["detections"].queryset = (
            FicheDetection.objects.all()
            .get_all_not_in_fiche_zone_delimitee(organisme_nuisible_libelle, fiche_zone_delimitee)
            .exclude_brouillon()
            .order_by_numero_fiche()
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
    def clean(self):
        super().clean()

        # Vérification des doublons de fiches détection dans les zones infestées
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

ZoneInfesteeFormSetUpdate = inlineformset_factory(
    FicheZoneDelimitee, ZoneInfestee, form=ZoneInfesteeForm, formset=ZoneInfesteeFormSet, extra=0, can_delete=False
)
