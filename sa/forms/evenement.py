import json

from django import forms
from django.conf import settings
from django.forms import Media, MultipleChoiceField
from django.utils import timezone
from django.utils.safestring import mark_safe
from django_countries.fields import CountryField
from dsfr.forms import DsfrBaseForm

from core.fields import MultiModelChoiceField, SEVESChoiceField
from core.form_mixins import WithFreeLinksMixin, js_module
from core.mixins import WithEtatMixin
from core.models import Departement
from core.widgets import TreeselectRadio
from sa.forms.fields import LatLonField
from sa.models import Espece, Maladie
from sa.models.evenement import (
    ContexteSuspicion,
    EvenementAnimal,
    Foyer,
    HumanInvolved,
    MesureDeControle,
    OrigineInfection,
    StatutAnimal,
    StatutEvenement,
    TypeDetenteur,
    TypeLieu,
)


class EvenementAnimalPreCreationForm(DsfrBaseForm):
    STATUT_ANIMAL_TOOLTIPS = {
        StatutAnimal.SAUVAGE: "Animal vivant à l'état naturel, non soumis à la surveillance humaine directe",
        StatutAnimal.DETENU: "Animal maintenu sous la responsabilité d'une personne (élevage, zoo, particulier, ruche…)",
    }

    maladie = forms.ModelChoiceField(
        queryset=Maladie.objects.all(),
        empty_label=settings.SELECT_EMPTY_CHOICE,
        required=True,
        widget=TreeselectRadio(
            choices=Maladie.treeselect_choices, attrs={"placeholder": "Rechercher", "required": True}
        ),
        label="Maladie suspectée",
    )
    espece = forms.ModelChoiceField(
        queryset=Espece.objects.all(),
        required=True,
        widget=TreeselectRadio(
            choices=Espece.treeselect_choices_for_maladie(None), attrs={"placeholder": "Rechercher", "required": True}
        ),
        label="Espèce",
    )
    statut_animal = forms.ChoiceField(
        required=True,
        choices=StatutAnimal,
        widget=forms.RadioSelect(attrs={"class": "fr-fieldset__element--inline"}),
        label="Statut de l'animal",
    )

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("sa/maladie_description_message.mjs"), js_module("sa/espece_grouping.mjs"))
        )

    @property
    def maladie_descriptions(self):
        return {str(maladie.pk): maladie.get_description_type_display() for maladie in self.fields["maladie"].queryset}

    @property
    def espece_options_by_maladie(self):
        default_frequent = [
            {"id": pk, "name": name}
            for pk, name in Espece.objects.filter(is_highlighted=True).order_by("name").values_list("pk", "name")
        ]

        maladie_queryset = self.fields["maladie"].queryset
        frequent_by_maladie = {}
        rows = (
            Espece.objects.filter(maladies_concernees__in=maladie_queryset)
            .values("pk", "name", "maladies_concernees")
            .order_by("name")
        )
        for row in rows:
            frequent_by_maladie.setdefault(row["maladies_concernees"], []).append(
                {"id": row["pk"], "name": row["name"]}
            )

        return {
            str(maladie.pk): {"frequent": frequent_by_maladie.get(maladie.pk, default_frequent)}
            for maladie in maladie_queryset
        }

    @property
    def all_especes(self):
        return [{"id": pk, "name": name} for pk, name in Espece.objects.order_by("name").values_list("pk", "name")]


class EvenementAnimalForm(DsfrBaseForm, WithFreeLinksMixin, forms.ModelForm):
    type_detenteur = forms.ChoiceField(
        choices=TypeDetenteur.choices,
        initial=TypeDetenteur.ETABLISSEMENT,
        required=True,
        widget=forms.RadioSelect,
    )

    statut_evenement = forms.ChoiceField(
        choices=StatutEvenement.choices,
        label=" Statut de l'événement",
        required=True,
        widget=forms.Select(attrs={"required": True}),
    )
    date_statut_changed = forms.DateField(
        required=True,
        label=mark_safe("<span class='label-marked'>Date à prendre en compte pour le changement de statut</span>"),
        help_text="À mettre à jour lors de la modification manuelle du statut",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )

    departement_etablissement = forms.ModelChoiceField(
        queryset=Departement.objects.order_by("numero").all(),
        to_field_name="numero",
        required=False,
        empty_label=settings.SELECT_EMPTY_CHOICE,
        label="Département",
    )
    pays_etablissement = CountryField(blank=True).formfield(
        label="Pays", empty_label=settings.SELECT_EMPTY_CHOICE, widget=forms.Select(attrs={"class": "fr-select"})
    )

    departement_particulier = forms.ModelChoiceField(
        queryset=Departement.objects.order_by("numero").all(),
        to_field_name="numero",
        required=False,
        empty_label=settings.SELECT_EMPTY_CHOICE,
        label="Département",
    )

    # Localisation
    adresse_lieu_dit = forms.CharField(
        label="Adresse ou lieu-dit", required=False, widget=forms.Select(attrs={"hidden": "hidden"})
    )
    type_lieu = SEVESChoiceField(
        choices=TypeLieu.choices,
        label="Type de lieu",
        widget=forms.Select(attrs={"required": True}),
    )
    coordinates = LatLonField(
        required=True,
        label="",
    )

    context_suspicion = forms.ChoiceField(
        choices=ContexteSuspicion.choices,
        required=False,
        widget=forms.RadioSelect(attrs={"class": "fr-fieldset__element--inline"}),
        label="Contexte de la suspicion",
        help_text="Contexte d'identification de la suspicion",
    )
    date_first_symptoms = forms.DateField(
        required=False,
        label="Date d'apparition des éventuels 1ers symptômes",
        help_text="À défaut date de la suspicion",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    human_involved = forms.ChoiceField(
        choices=HumanInvolved.choices,
        widget=forms.RadioSelect(attrs={"class": "fr-fieldset__element--inline"}),
        label="Humains exposés pour lesquels des actions sont engagées ?",
        required=False,
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "cols": 30,
                "rows": 10,
                "placeholder": "Circonstances de la suspicion, investigations engagées, précisions sur la date des symptômes ou sur les conditions du prélèvement",
            }
        ),
        label="Description de la situation",
    )
    # Enquête épidémiologique
    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "cols": 30,
                "rows": 5,
                "placeholder": "Informations sur les déplacements de l'animal, les animaux ou personnes en contact.",
            }
        ),
        label="Commentaire",
    )

    # Mesures de gestion
    date_apms = forms.DateField(
        required=False,
        label="Date APMS",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    date_apdi = forms.DateField(
        required=False,
        label="Date APDI",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    date_levee = forms.DateField(
        required=False,
        label="Date levée APMS ou APDI",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    date_d_zero = forms.DateField(
        required=False,
        label="Date D zéro",
        help_text="Date de la désinfection préliminaire (maladies cat. A)",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    date_nd1 = forms.DateField(
        required=False,
        label="Date ND1",
        help_text="Date du premier nettoyage de désinfection (maladies cat. A)",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    date_nd2 = forms.DateField(
        required=False,
        label="Date ND2",
        help_text="Date du deuxième nettoyage de désinfection (maladies cat. A)",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    date_nd = forms.DateField(
        required=False,
        label="Date ND",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )

    foyer = forms.ChoiceField(choices=Foyer.choices, required=False, widget=forms.RadioSelect, label="Foyer")
    date_notification_adis = forms.DateField(
        required=False,
        label="Date notification ADIS",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    date_cloture_adis = forms.DateField(
        required=False,
        label="Date clôture ADIS",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )
    origine_infection = SEVESChoiceField(
        required=False, label="Origine de l'infection", choices=OrigineInfection.choices
    )
    mesures_controle = MultipleChoiceField(
        choices=MesureDeControle.choices, label="Mesures de contrôle mises en œuvre", required=False
    )

    typage_niveau_2 = forms.ChoiceField(required=False, choices=())
    typage_niveau_3 = forms.ChoiceField(required=False, choices=())

    @property
    def media(self):
        return super().media + Media(
            js=(
                js_module("core/map.mjs"),
                js_module("core/address_search_autocomplete.mjs"),
                js_module("core/siret.mjs"),
                js_module("sa/detenteur.mjs"),
                js_module("sa/localisation_from_detenteur.mjs"),
                js_module("sa/adis.mjs"),
                js_module("sa/typage.mjs"),
                js_module("ssa/free_links.mjs"),
            ),
        )

    class Meta:
        model = EvenementAnimal

        adis_fields = [
            "foyer",
            "numero_adis",
            "date_notification_adis",
            "date_cloture_adis",
            "effectif_retenu",
            "origine_infection",
            "mesures_controle",
        ]

        detenteur_fields = [
            # Détenteur etablissement
            "numero_identifiant_etablissement",
            "raison_sociale_etablissement",
            "departement_etablissement",
            "autre_identifiant_etablissement",
            "adresse_lieu_dit_etablissement",
            "code_insee_etablissement",
            "siret_etablissement",
            "commune_etablissement",
            "pays_etablissement",
            # Détenteur particulier
            "nom_particulier",
            "prenom_particulier",
            "adresse_particulier",
            "commune_particulier",
            "departement_particulier",
            "code_insee_particulier",
            "email_particulier",
            "telephone_particulier",
        ]

        fields = [
            "maladie",
            "espece",
            "statut_animal",
            "statut_evenement",
            "date_statut_changed",
            *detenteur_fields,
            # Localisation
            "adresse_lieu_dit",
            "commune",
            "code_insee",
            "numero_identifiant",
            "type_lieu",
            "coordinates",
            "context_suspicion",
            "date_first_symptoms",
            "human_involved",
            "description",
            # Enquete epidémiologique
            "commentaire",
            # Typage
            "typage_champ_libre",
            # Mesures de gestion
            "date_apms",
            "date_apdi",
            "date_levee",
            "date_d_zero",
            "date_nd1",
            "date_nd2",
            "date_nd",
            # Adis
            *adis_fields,
        ]
        widgets = {
            "maladie": forms.HiddenInput,
            "espece": forms.HiddenInput,
            "statut_animal": forms.HiddenInput,
            "code_insee": forms.HiddenInput,
            "commune": forms.Select(attrs={"hidden": "hidden"}),
            "siret_etablissement": forms.Select(attrs={"hidden": "hidden"}),
            "adresse_lieu_dit_etablissement": forms.Select(attrs={"hidden": "hidden"}),
            "commune_etablissement": forms.Select(attrs={"hidden": "hidden"}),
            "adresse_particulier": forms.Select(attrs={"hidden": "hidden"}),
            "commune_particulier": forms.Select(attrs={"hidden": "hidden"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.maladie_id = kwargs.pop("maladie")
        self.espece = kwargs.pop("espece")
        self.statut_animal = kwargs.pop("statut_animal")
        self.structure = kwargs.pop("structure")
        super().__init__(*args, **kwargs)
        self._add_free_links(model=EvenementAnimal)
        self.fields["maladie"].initial = self.maladie_id
        self.maladie = Maladie.objects.get(id=self.maladie_id)
        self._init_typage_fields()
        self.fields["espece"].initial = self.espece
        self.fields["statut_animal"].initial = self.statut_animal
        self.fields["type_lieu"].choices = (
            ("", settings.SELECT_EMPTY_CHOICE),
            *TypeLieu.choices_for_statut_animal(self.statut_animal),
        )

        today = timezone.localtime(timezone.now()).date().isoformat()
        self.fields["date_statut_changed"].widget.attrs["max"] = today
        self.fields["date_first_symptoms"].widget.attrs["max"] = today
        self.fields["date_notification_adis"].widget.attrs["max"] = today
        self.fields["date_cloture_adis"].widget.attrs["max"] = today

        type_detenteur = self.fields["type_detenteur"].initial
        if self.is_bound:
            type_detenteur = self.data.get("type_detenteur")

        if not self.maladie.needs_arrete:
            self.fields.pop("date_apms")
            self.fields.pop("date_apdi")
            self.fields.pop("date_levee")

        if self.maladie.needs_dates_desinfection is False:
            self.fields.pop("date_d_zero")
            self.fields.pop("date_nd1")
            self.fields.pop("date_nd2")

        if self.maladie.needs_date_nd is False:
            self.fields.pop("date_nd")

        if self.user.agent.structure.is_ac is False:
            for field in self.Meta.adis_fields:
                self.fields.pop(field)

        if self.show_detenteur_block is True:
            if type_detenteur == TypeDetenteur.PARTICULIER:
                self.fields["numero_identifiant_etablissement"].required = False
                self.fields["nom_particulier"].required = True
            else:
                self.fields["numero_identifiant_etablissement"].required = True
                self.fields["nom_particulier"].required = False
        else:
            self.fields.pop("type_detenteur")
            for field in self.Meta.detenteur_fields:
                self.fields.pop(field)

    def _init_typage_fields(self):
        self.niveaux3_par_niveau2 = {}
        self["typage_champ_libre"].label = self.maladie.intitule_typage_champ_libre

        if not self.is_bound and self.instance.typage_id:
            self.initial["typage_niveau_2"] = self.instance.typage.valeur_niveau_2
            self.initial["typage_niveau_3"] = self.instance.typage.valeur_niveau_3

        typage_queryset = self.maladie.typages.all()
        niveau_2_values = list(
            dict.fromkeys(typage_queryset.exclude(valeur_niveau_2="").values_list("valeur_niveau_2", flat=True))
        )
        if not niveau_2_values:
            self.fields.pop("typage_niveau_2")
            self.fields.pop("typage_niveau_3")
            return

        self.fields["typage_niveau_2"].choices = (
            ("", settings.SELECT_EMPTY_CHOICE),
            *((value, value) for value in niveau_2_values),
        )
        self["typage_niveau_2"].label = self.maladie.intitule_typage_niveau_2

        queryset = (
            typage_queryset.exclude(valeur_niveau_2="")
            .exclude(valeur_niveau_3="")
            .values_list("valeur_niveau_2", "valeur_niveau_3")
        )
        for valeur_niveau_2, valeur_niveau_3 in queryset:
            self.niveaux3_par_niveau2.setdefault(valeur_niveau_2, [])
            if valeur_niveau_3 not in self.niveaux3_par_niveau2[valeur_niveau_2]:
                self.niveaux3_par_niveau2[valeur_niveau_2].append(valeur_niveau_3)

        if not self.niveaux3_par_niveau2:
            self.fields.pop("typage_niveau_3")
            return

        niveau_3_submitted = self.initial.get("typage_niveau_3")
        if self.is_bound:
            niveau_3_submitted = self.data.get(self.add_prefix("typage_niveau_3")) or niveau_3_submitted
        niveau_3_choices = [("", settings.SELECT_EMPTY_CHOICE)]
        if niveau_3_submitted and (niveau_3_submitted, niveau_3_submitted) not in niveau_3_choices:
            niveau_3_choices.append((niveau_3_submitted, niveau_3_submitted))
        self.fields["typage_niveau_3"].choices = niveau_3_choices
        self["typage_niveau_3"].label = self.maladie.intitule_typage_niveau_3

    @property
    def typage_niveaux3_par_niveau2_json(self):
        return json.dumps(self.niveaux3_par_niveau2)

    @property
    def show_detenteur_block(self):
        return self.statut_animal == StatutAnimal.DETENU

    @property
    def show_mesures_first_row(self):
        return self.maladie.needs_arrete

    @property
    def show_mesures_second_row(self):
        return self.maladie.needs_dates_desinfection

    @property
    def show_mesures_third_row(self):
        return self.maladie.needs_date_nd

    @property
    def show_mesures_block(self):
        return self.show_mesures_first_row or self.show_mesures_second_row or self.show_mesures_third_row

    def save(self, commit=True):
        if self.data.get("action") == "publish":
            self.instance.etat = WithEtatMixin.Etat.EN_COURS
            self.instance.date_publication = timezone.now()
        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        self.save_free_links(instance)
        return instance

    def clean(self):
        cleaned_data = super().clean()
        type_detenteur = cleaned_data.get("type_detenteur")

        if type_detenteur == TypeDetenteur.ETABLISSEMENT:
            particulier_fields = (
                "nom_particulier",
                "prenom_particulier",
                "adresse_particulier",
                "commune_particulier",
                "departement_particulier",
                "code_insee_particulier",
                "email_particulier",
                "telephone_particulier",
            )
            for field in particulier_fields:
                self.cleaned_data.pop(field, None)
        elif type_detenteur == TypeDetenteur.PARTICULIER:
            etablissement_fields = (
                "numero_identifiant_etablissement",
                "raison_sociale_etablissement",
                "departement_etablissement",
                "autre_identifiant_etablissement",
                "adresse_lieu_dit_etablissement",
                "code_insee_etablissement",
                "siret_etablissement",
                "commune_etablissement",
                "pays_etablissement",
            )
            for field in etablissement_fields:
                self.cleaned_data.pop(field, None)

        if "typage_niveau_2" in self.fields:
            valeur_niveau_2 = cleaned_data.get("typage_niveau_2") or ""
            valeur_niveau_3 = cleaned_data.get("typage_niveau_3") or ""
            sous_types = self.niveaux3_par_niveau2.get(valeur_niveau_2, [])
            if valeur_niveau_3 and valeur_niveau_3 not in sous_types:
                cleaned_data["typage_niveau_3"] = ""
                valeur_niveau_3 = ""
            if sous_types and not valeur_niveau_3:
                self.add_error("typage_niveau_3", "Sélection obligatoire pour ce typage.")
            elif valeur_niveau_2:
                typage = self.maladie.typages.filter(
                    valeur_niveau_2=valeur_niveau_2, valeur_niveau_3=valeur_niveau_3
                ).first()
                if typage is None:
                    self.add_error("typage_niveau_2", "Sélection invalide pour cette maladie.")
                else:
                    self.instance.typage = typage
            else:
                self.instance.typage = None

        return cleaned_data

    def get_queryset(self, model, user, instance):
        return (
            EvenementAnimal.objects.all()
            .order_by_numero()
            .get_user_can_view(user)
            .exclude(id=instance.id)
            .exclude(etat=EvenementAnimal.Etat.BROUILLON)
        )

    def _add_free_links(self, model):
        instance = getattr(self, "instance", None)
        if self.is_bound:
            choices = [(self.model_label, self.get_queryset(model, self.user, instance))]
        else:
            choices = []
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=choices,
        )
