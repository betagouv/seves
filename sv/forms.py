import datetime

from core.forms import DSFRForm, VisibiliteUpdateBaseForm

from core.fields import MultiModelChoiceField
from django import forms
from django.forms.models import inlineformset_factory
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.utils.translation import ngettext
from django.forms import BaseInlineFormSet
from django.db.models import TextChoices

from core.models import LienLibre
from core.fields import DSFRRadioButton
from sv.models import (
    FicheZoneDelimitee,
    ZoneInfestee,
    OrganismeNuisible,
    StatutReglementaire,
    FicheDetection,
    Lieu,
    Prelevement,
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


class LieuForm(DSFRForm, forms.ModelForm):
    # TODO handle this properly, see how we can do this
    nom = forms.CharField(widget=forms.TextInput(attrs={"required": "true"}))
    commune = forms.CharField(widget=forms.HiddenInput(), required=False)
    code_insee = forms.CharField(widget=forms.HiddenInput(), required=False)
    departement = forms.CharField(widget=forms.HiddenInput(), required=False)
    wgs84_longitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": 0.000001,
                "min": "-180",
                "max": "180",
                "style": "flex: 0.55; margin-right: .5rem;",
                "placeholder": "Latitude",
            }
        ),
    )
    wgs84_latitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": 0.000001,
                "min": "-90",
                "max": "90",
                "style": "flex: 0.55; margin-top: .5rem;",
                "placeholder": "Longitude",
            }
        ),
    )
    lambert93_latitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": 1,
                "min": "6000000",
                "max": "7200000",
                "style": "flex: 0.55; margin-right: .5rem;",
                "placeholder": "Latitude",
            }
        ),
    )
    lambert93_longitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": 1,
                "min": "200000",
                "max": "1200000",
                "style": "flex: 0.55; margin-top: .5rem;",
                "placeholder": "Longitude",
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


LieuFormSet = inlineformset_factory(FicheDetection, Lieu, form=LieuForm, extra=10, can_delete=True)


class PrelevementForm(DSFRForm, forms.ModelForm):
    # TODO when this is created as detecté the object is non detecté
    resultat = forms.ChoiceField(
        required=True,
        choices=Prelevement.Resultat.choices,
        widget=DSFRRadioButton(),
    )

    class Meta:
        model = Prelevement
        exclude = []

    def __init__(self, *args, **kwargs):
        # TODO better naming for this ?
        by_pass_required = kwargs.pop("by_pass_required", False)
        super().__init__(*args, **kwargs)
        # TODO add other required fields
        self.fields["structure_preleveur"].widget.attrs["required"] = "required"

        if by_pass_required:
            for field in self:
                if field.field.required:
                    field.field.widget.attrs["data-required"] = "true"
                    field.field.required = False


class FicheDetectionForm(DSFRForm, forms.ModelForm):
    vegetaux_infestes = forms.CharField(max_length=500, required=False, widget=forms.Textarea(attrs={"rows": ""}))
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={"rows": ""}),
        required=False,
    )
    mesures_conservatoires_immediates = forms.CharField(
        widget=forms.Textarea(attrs={"rows": ""}),
        required=False,
    )
    mesures_consignation = forms.CharField(
        widget=forms.Textarea(attrs={"rows": ""}),
        required=False,
    )
    mesures_phytosanitaires = forms.CharField(
        widget=forms.Textarea(attrs={"rows": ""}),
        required=False,
    )
    mesures_surveillance_specifique = forms.CharField(widget=forms.Textarea(attrs={"rows": ""}), required=False)
    date_premier_signalement = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"max": datetime.date.today(), "type": "date"})
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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")

        super().__init__(*args, **kwargs)

        if not self.user.agent.structure.is_ac:
            self.fields.pop("numero_europhyt")
            self.fields.pop("numero_rasff")

        self._add_free_links()

        # if self.instance.pk:
        #     self.fields.pop("visibilite")

    # TODO factorize all this with other form
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

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.createur = self.user.agent.structure
        if commit:
            instance.save()
            self.save_free_links(instance)
        return instance

    def _add_free_links(self):
        qs_detection = FicheDetection.objects.all().order_by_numero_fiche().get_fiches_user_can_view(self.user)
        qs_detection = qs_detection.select_related("numero")
        qs_zone = FicheZoneDelimitee.objects.all().order_by_numero_fiche().get_fiches_user_can_view(self.user)
        qs_zone = qs_zone.select_related("numero")
        if self.instance:
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

        qs_detection = FicheDetection.objects.all().order_by_numero_fiche().get_fiches_user_can_view(self.user)
        qs_detection = qs_detection.select_related("numero")
        qs_zone = FicheZoneDelimitee.objects.all().order_by_numero_fiche().get_fiches_user_can_view(self.user)
        qs_zone = qs_zone.select_related("numero")
        if self.instance:
            qs_zone = qs_zone.exclude(id=self.instance.id)
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=[
                ("Fiche Détection", qs_detection),
                ("Fiche zone délimitée", qs_zone),
            ],
        )

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

    def clean_free_link(self):
        if self.instance and self.instance in self.cleaned_data["free_link"]:
            raise ValidationError("Vous ne pouvez pas lier une fiche a elle-même.")
        return self.cleaned_data["free_link"]

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
