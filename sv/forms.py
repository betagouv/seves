import datetime
from copy import copy

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django.forms.models import inlineformset_factory
from django.utils.timezone import now
from django.utils.translation import ngettext
from django_countries.fields import CountryField

from core.constants import AC_STRUCTURE, MUS_STRUCTURE, BSV_STRUCTURE
from core.fields import DSFRRadioButton, DSFRCheckboxSelectMultiple
from core.form_mixins import DSFRForm
from core.forms import VisibiliteUpdateBaseForm, BaseMessageForm
from core.models import Structure, Visibilite, Message, Contact
from sv.form_mixins import (
    WithDataRequiredConversionMixin,
    WithLatestVersionLocking,
    WithEvenementFreeLinksMixin,
)
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
    Evenement,
)


class EvenementVisibiliteUpdateForm(VisibiliteUpdateBaseForm, forms.ModelForm):
    class Meta:
        model = Evenement
        fields = ["visibilite"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["visibilite"].choices = [
            (value, Visibilite.get_masculine_label(value)) for value, _ in Visibilite.choices
        ]


class DepartementModelChoiceField(forms.ModelChoiceField):
    def prepare_value(self, value):
        try:
            if str(value).isdigit():
                return Departement.objects.get(id=value).numero
        except Departement.DoesNotExist:
            pass
        return super().prepare_value(value)


class AdresseLieuDitField(forms.ChoiceField):
    def validate(self, value):
        # Autorise n'importe quelle valeur
        return


class LieuForm(DSFRForm, WithDataRequiredConversionMixin, forms.ModelForm):
    nom = forms.CharField(widget=forms.TextInput(), required=True)
    adresse_lieu_dit = AdresseLieuDitField(choices=[], required=False)
    commune = forms.CharField(widget=forms.HiddenInput(), required=False)
    code_insee = forms.CharField(widget=forms.HiddenInput(), required=False)
    departement = DepartementModelChoiceField(
        queryset=Departement.objects.all(),
        to_field_name="numero",
        required=False,
        widget=forms.Select(attrs={"class": "fr-hidden"}),
    )
    wgs84_longitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "wgs-longitude-field",
                "placeholder": "Longitude",
            }
        ),
    )
    wgs84_latitude = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "wgs-latitude-field",
                "placeholder": "Latitude",
            }
        ),
    )
    activite_etablissement = forms.CharField(
        required=False,
        label="Description de l’activité",
        widget=forms.Textarea(
            attrs={
                "rows": 2,
                "maxlength": 100,
                "title": "Ce champ est limité à 100 caractères.",
            }
        ),
    )
    siret_etablissement = forms.CharField(
        required=False,
        max_length=14,
        label="N° SIRET",
        widget=forms.TextInput(
            attrs={
                "pattern": "[0-9]{14}",
                "placeholder": "110 070 018 00012",
                "title": "Le Siret doit contenir exactement 14 chiffres",
            }
        ),
    )
    adresse_etablissement = AdresseLieuDitField(choices=[], required=False, label="Adresse ou lieu-dit")
    departement_etablissement = DepartementModelChoiceField(
        queryset=Departement.objects.all(),
        to_field_name="numero",
        required=False,
        label="Département",
    )
    code_insee_etablissement = forms.CharField(widget=forms.HiddenInput(), required=False)
    pays_etablissement = CountryField(blank=True).formfield(label="Pays")

    class Meta:
        model = Lieu
        exclude = []
        labels = {
            "is_etablissement": "Il s'agit d'un établissement",
            "raison_sociale_etablissement": "Raison sociale",
        }

    def clean_departement(self):
        if self.cleaned_data["departement"] == "":
            return None
        return self.cleaned_data["departement"]

    def __init__(self, *args, **kwargs):
        convert_required_to_data_required = kwargs.pop("convert_required_to_data_required", False)
        super().__init__(*args, **kwargs)

        if not self.is_bound and self.instance and self.instance.pk and self.instance.adresse_lieu_dit:
            if self.instance.adresse_lieu_dit:
                choice = (self.instance.adresse_lieu_dit, self.instance.adresse_lieu_dit)
                self.fields["adresse_lieu_dit"].choices = [choice]
            if self.instance.adresse_etablissement:
                choice = (self.instance.adresse_etablissement, self.instance.adresse_etablissement)
                self.fields["adresse_etablissement"].choices = [choice]

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


class SelectWithAttributeField(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            confirmation_officielle = value.instance.confirmation_officielle
            option["attrs"]["data-confirmation-officielle"] = "true" if confirmation_officielle else "false"
            if (
                self.form_instance.instance.type_analyse == Prelevement.TypeAnalyse.CONFIRMATION
                and not confirmation_officielle
            ):
                option["attrs"]["disabled"] = "disabled"
        return option


class PrelevementForm(DSFRForm, WithDataRequiredConversionMixin, forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    resultat = forms.ChoiceField(
        required=True,
        choices=Prelevement.Resultat.choices,
        widget=DSFRRadioButton(attrs={"required": "true", "class": "fr-fieldset__element--inline"}),
    )
    type_analyse = forms.ChoiceField(
        required=True,
        choices=Prelevement.TypeAnalyse.choices,
        widget=DSFRRadioButton(attrs={"required": "true", "class": "fr-fieldset__element--inline fr-mb-0"}),
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
        widgets = {
            "numero_rapport_inspection": forms.TextInput(
                attrs={
                    "placeholder": "24-123456",
                    "pattern": r"^\d{2}-\d{6}$",
                    "title": "Format attendu : AA-XXXXXX où AA correspond à l'année sur 2 chiffres (ex: 24 pour 2024) et XXXXXX est un numéro à 6 chiffres",
                }
            ),
            "laboratoire": SelectWithAttributeField,
            "date_prelevement": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "date_rapport_analyse": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        convert_required_to_data_required = kwargs.pop("convert_required_to_data_required", False)
        cached_choices = kwargs.pop("cached_choices", {})
        labo_values = kwargs.pop("labo_values", None)
        structure_values = kwargs.pop("structure_values", None)
        super().__init__(*args, **kwargs)

        self.fields["laboratoire"].widget.form_instance = self

        for field_name, choices in cached_choices.items():
            if choices is not None and field_name in self.fields:
                self.fields[field_name].choices = choices

        if labo_values:
            self.fields["laboratoire"].queryset = labo_values
        if structure_values:
            self.fields["structure_preleveuse"].queryset = structure_values

        if convert_required_to_data_required:
            self._convert_required_to_data_required()

    def clean_espece_echantillon(self):
        if self.cleaned_data["espece_echantillon"]:
            return EspeceEchantillon.objects.get(pk=self.cleaned_data["espece_echantillon"])

    def clean(self):
        super().clean()
        if self.cleaned_data["is_officiel"] is False:
            self.cleaned_data["numero_rapport_inspection"] = ""
            self.cleaned_data["laboratoire"] = None


class FicheDetectionForm(DSFRForm, WithLatestVersionLocking, forms.ModelForm):
    vegetaux_infestes = forms.CharField(
        label="Quantité de végétaux infestés", max_length=500, required=False, widget=forms.Textarea(attrs={"rows": ""})
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
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    statut_reglementaire = forms.ModelChoiceField(
        label="Statut réglementaire", queryset=StatutReglementaire.objects.all(), required=True
    )
    organisme_nuisible = forms.ModelChoiceField(
        label="Organisme nuisible", queryset=OrganismeNuisible.objects.all(), required=True
    )

    class Meta:
        model = FicheDetection
        fields = [
            "statut_evenement",
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
            "latest_version",
        ]
        labels = {"statut_evenement": "Statut évènement"}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["date_premier_signalement"].widget.attrs["max"] = datetime.date.today().isoformat()

        if (kwargs.get("data") and kwargs.get("data").get("evenement")) or (
            self.instance.pk and self.instance.evenement
        ):
            self.fields.pop("organisme_nuisible")
            self.fields.pop("statut_reglementaire")

        for field_name, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField):
                field.empty_label = settings.SELECT_EMPTY_CHOICE

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.createur = self.user.agent.structure
        if commit:
            instance.save()
        return instance


class FicheZoneDelimiteeForm(DSFRForm, WithLatestVersionLocking, forms.ModelForm):
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
        }
        widgets = {
            "createur": forms.HiddenInput,
            "vegetaux_infestes": forms.Textarea(attrs={"rows": 1}),
            "commentaire": forms.Textarea(attrs={"rows": 3}),
            "rayon_zone_tampon": forms.NumberInput(attrs={"min": "0"}),
            "surface_tampon_totale": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.detections_zones_infestees_formset = kwargs.pop("detections_zones_infestees_formset", None)

        super().__init__(*args, **kwargs)

        if evenement := self.initial.get("evenement"):
            queryset = FicheDetection.objects.filter(evenement=evenement)
        elif self.instance.pk:
            queryset = FicheDetection.objects.all().get_all_not_in_fiche_zone_delimitee(self.instance)

        self.fields["detections_hors_zone"].queryset = queryset.order_by_numero_fiche()

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
        return sorted([d.numero for d in duplicate_fiches_detection])

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
        widgets = {
            "rayon": forms.NumberInput(attrs={"min": "0"}),
            "surface_infestee_totale": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        evenement = kwargs.pop("evenement")
        fiche_zone_delimitee = kwargs.pop("fiche_zone_delimitee", None)

        super().__init__(*args, **kwargs)

        fiche_zone_delimitee = (
            self.instance.fiche_zone_delimitee
            if not fiche_zone_delimitee and self.instance.fiche_zone_delimitee_id
            else fiche_zone_delimitee
        )

        self.fields["detections"].queryset = FicheDetection.objects.filter(evenement=evenement).order_by_numero_fiche()

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
    FicheZoneDelimitee, ZoneInfestee, form=ZoneInfesteeForm, formset=ZoneInfesteeFormSet, extra=1, can_delete=True
)

ZoneInfesteeFormSetUpdate = inlineformset_factory(
    FicheZoneDelimitee, ZoneInfestee, form=ZoneInfesteeForm, formset=ZoneInfesteeFormSet, extra=0, can_delete=True
)


class EvenementForm(DSFRForm, forms.ModelForm):
    class Meta:
        model = Evenement
        fields = [
            "organisme_nuisible",
            "statut_reglementaire",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.createur = self.user.agent.structure
        if commit:
            instance.save()
        return instance


class EvenementUpdateForm(DSFRForm, WithEvenementFreeLinksMixin, WithLatestVersionLocking, forms.ModelForm):
    class Meta:
        model = Evenement
        fields = [
            "organisme_nuisible",
            "statut_reglementaire",
            "latest_version",
            "numero_europhyt",
            "numero_rasff",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self._add_free_links(model=Evenement)
        if not self.user.agent.structure.is_ac:
            self.fields.pop("numero_europhyt")
            self.fields.pop("numero_rasff")

    def save(self, commit=True):
        instance = super().save(commit)
        self.save_free_links(instance)
        return instance


class StructureSelectionForVisibiliteForm(forms.ModelForm, DSFRForm):
    allowed_structures = forms.ModelMultipleChoiceField(
        queryset=Structure.objects.none(),
        required=True,
        label="",
        widget=DSFRCheckboxSelectMultiple(attrs={"class": "fr-checkbox-group"}),
    )

    class Meta:
        model = Evenement
        fields = ["allowed_structures"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        structures_queryset = Structure.objects.has_at_least_one_active_contact().distinct()
        self.fields["allowed_structures"].queryset = structures_queryset

        # Initialiser les structures présélectionnées et désactivées
        mus_bsv = structures_queryset.filter(niveau1=AC_STRUCTURE, niveau2__in=[MUS_STRUCTURE, BSV_STRUCTURE])
        structures_disabled = list(mus_bsv) + [self.instance.createur]
        disabled_pks = [structure.pk for structure in structures_disabled]
        self.fields["allowed_structures"].widget.disabled_choices = disabled_pks
        self.fields["allowed_structures"].widget.checked_choices = disabled_pks


class MessageForm(BaseMessageForm):
    recipients_limited_recipients = forms.MultipleChoiceField(
        choices=[("mus", "MUS"), ("bsv", "BSV")],
        label="Destinataires",
        widget=DSFRCheckboxSelectMultiple(attrs={"class": "fr-checkbox-group"}),
    )
    manual_render_fields = [
        "recipients_structures_only",
        "recipients_copy_structures_only",
        "recipients_limited_recipients",
    ]

    class Meta(BaseMessageForm.Meta):
        fields = [
            "recipients",
            "recipients_structures_only",
            "recipients_copy",
            "recipients_copy_structures_only",
            "recipients_limited_recipients",
            "message_type",
            "title",
            "content",
            "content_type",
            "object_id",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        kwargs["limit_contacts_to"] = "sv"
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance and instance.pk and "recipients_limited_recipients" in self.fields:
            self.fields["recipients_limited_recipients"].widget.attrs["id"] = (
                f"id_recipients_limited_recipients_{instance.pk}"
            )
            recipients = self.instance.recipients.values_list("structure__libelle", flat=True)
            if recipients:
                initial = [r.lower() for r in recipients if r]
                self.initial["recipients_limited_recipients"] = initial

    def _convert_checkboxes_to_contacts(self):
        try:
            checkboxes = copy(self.cleaned_data["recipients_limited_recipients"])
        except KeyError:
            raise ValidationError("Au moins un destinataire doit être sélectionné.")
        self.cleaned_data["recipients"] = []
        if "mus" in checkboxes:
            self.cleaned_data["recipients"].append(Contact.objects.get_mus())
        if "bsv" in checkboxes:
            self.cleaned_data["recipients"].append(Contact.objects.get_bsv())

    def clean(self):
        super().clean()
        if self.cleaned_data["message_type"] in Message.TYPES_WITH_LIMITED_RECIPIENTS:
            self._convert_checkboxes_to_contacts()
