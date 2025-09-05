from django import forms
from django.forms import Media
from django.utils import timezone
from dsfr.forms import DsfrBaseForm

from core.fields import SEVESChoiceField, MultiModelChoiceField, ContactModelMultipleChoiceField
from core.form_mixins import WithFreeLinksMixin, js_module
from core.forms import BaseEtablissementForm
from core.forms import BaseMessageForm
from core.mixins import WithEtatMixin
from core.mixins import WithSireneTokenMixin
from core.models import Contact, Message, Structure
from ssa.models import EvenementProduit
from tiac.constants import EvenementOrigin, EvenementFollowUp
from tiac.constants import ModaliteDeclarationEvenement
from tiac.models import EvenementSimple, Etablissement, InvestigationTiac, TypeEvenement


class EvenementSimpleForm(DsfrBaseForm, WithFreeLinksMixin, forms.ModelForm):
    date_reception = forms.DateTimeField(
        required=False,
        label="Date de réception à la DD(ETS)PP",
        widget=forms.DateInput(format="%d/%m/%Y", attrs={"type": "date", "value": timezone.now().strftime("%Y-%m-%d")}),
    )
    evenement_origin = SEVESChoiceField(
        choices=EvenementOrigin.choices,
        label="Signalement déclaré par",
        required=False,
    )
    nb_sick_persons = forms.IntegerField(required=False, label="Nombre de malades total")
    follow_up = forms.ChoiceField(
        choices=EvenementFollowUp.choices, widget=forms.RadioSelect, label="Suite donnée par la DD", required=True
    )
    modalites_declaration = forms.ChoiceField(
        required=False,
        choices=ModaliteDeclarationEvenement.choices,
        widget=forms.RadioSelect,
        label="Modalités de déclaration",
    )

    class Meta:
        model = EvenementSimple
        fields = (
            "date_reception",
            "evenement_origin",
            "modalites_declaration",
            "contenu",
            "notify_ars",
            "nb_sick_persons",
            "follow_up",
        )
        widgets = {
            "notify_ars": forms.RadioSelect(choices=(("true", "Oui"), ("false", "Non"))),
        }

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("core/free_links.mjs"),),
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self._add_free_links()

    def save(self, commit=True):
        if self.data.get("action") == "publish":
            self.instance.etat = WithEtatMixin.Etat.EN_COURS

        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        self.save_free_links(instance)
        return instance

    def _add_free_links(self, model=None):
        instance = getattr(self, "instance", None)

        queryset = (
            EvenementSimple.objects.all()
            .order_by_numero()
            .get_user_can_view(self.user)
            .exclude(etat=EvenementSimple.Etat.BROUILLON)
        )
        if instance:
            queryset = queryset.exclude(id=instance.id)

        queryset_evenement_produit = (
            EvenementProduit.objects.all()
            .order_by_numero()
            .get_user_can_view(self.user)
            .exclude(etat=EvenementProduit.Etat.BROUILLON)
        )
        self.fields["free_link"] = MultiModelChoiceField(
            required=False,
            label="Sélectionner un objet",
            model_choices=[
                ("Enregistrement simple", queryset),
                ("Évenement produit", queryset_evenement_produit),
            ],
        )


class MessageForm(BaseMessageForm):
    recipients_limited_recipients = ContactModelMultipleChoiceField(
        queryset=Contact.objects.get_tiac_structures(), label="Destinataires", required=False
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
        kwargs["limit_contacts_to"] = "ssa"
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.cleaned_data["message_type"] in Message.TYPES_WITH_LIMITED_RECIPIENTS:
            self.cleaned_data["recipients"] = self.cleaned_data["recipients_limited_recipients"]


class EtablissementForm(WithSireneTokenMixin, DsfrBaseForm, BaseEtablissementForm, forms.ModelForm):
    template_name = "tiac/forms/etablissement.html"

    siret = forms.CharField(
        label="N° SIRET",
        label_suffix="",
        required=False,
        max_length=14,
        widget=forms.Select(attrs={"hidden": "hidden"}),
    )
    type_etablissement = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Lieu d'achat, restaurant, centre d'expédition..."}),
    )

    class Meta:
        model = Etablissement
        fields = [
            "type_etablissement",
            "siret",
            "raison_sociale",
            "enseigne_usuelle",
            "adresse_lieu_dit",
            "commune",
            "code_insee",
            "departement",
            "pays",
        ]
        widgets = {"code_insee": forms.HiddenInput}


class EvenementSimpleTransferForm(DsfrBaseForm, forms.ModelForm):
    transfered_to = forms.ModelChoiceField(
        queryset=Structure.objects.only_DD(),
        label="Sélectionner une structure",
        required=True,
    )

    class Meta:
        model = EvenementSimple
        fields = ["transfered_to"]


class InvestigationTiacForm(DsfrBaseForm, WithFreeLinksMixin, forms.ModelForm):
    date_reception = forms.DateTimeField(
        required=False,
        label="Date de réception à la DD(ETS)PP",
        widget=forms.DateInput(format="%d/%m/%Y", attrs={"type": "date", "value": timezone.now().strftime("%Y-%m-%d")}),
    )
    evenement_origin = SEVESChoiceField(
        choices=EvenementOrigin.choices,
        label="Signalement déclaré par",
        required=False,
    )
    modalites_declaration = forms.ChoiceField(
        required=False,
        choices=ModaliteDeclarationEvenement.choices,
        widget=forms.RadioSelect,
        label="Modalités de déclaration",
    )
    type_evenement = forms.ChoiceField(
        choices=TypeEvenement.choices, widget=forms.RadioSelect, label="Type d'événement", required=True
    )

    nb_sick_persons = forms.IntegerField(required=False, label="Nombre de malades total")
    nb_sick_persons_to_hospital = forms.IntegerField(required=False, label="Dont conduits à l'hôpital")
    nb_dead_persons = forms.IntegerField(required=False, label="Dont décédés")
    datetime_first_symptoms = forms.DateTimeField(
        required=False,
        label="Première date et heure d'apparition des symptômes",
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
                "value": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            },
        ),
    )

    datetime_last_symptoms = forms.DateTimeField(
        required=False,
        label="Dernière date et heure d'apparition des symptômes",
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
                "value": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            },
        ),
    )

    class Meta:
        model = InvestigationTiac
        fields = (
            "date_reception",
            "evenement_origin",
            "modalites_declaration",
            "contenu",
            "notify_ars",
            "will_trigger_inquiry",
            "numero_sivss",
            "type_evenement",
            "nb_sick_persons",
            "nb_sick_persons_to_hospital",
            "nb_dead_persons",
            "datetime_first_symptoms",
            "datetime_last_symptoms",
        )
        widgets = {
            "notify_ars": forms.RadioSelect(choices=(("true", "Oui"), ("false", "Non"))),
            "will_trigger_inquiry": forms.RadioSelect(choices=(("true", "Oui"), ("false", "Non"))),
        }

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("core/free_links.mjs"),),
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        if self.data.get("action") == "publish":
            self.instance.etat = WithEtatMixin.Etat.EN_COURS

        if not self.instance.pk:
            self.instance.createur = self.user.agent.structure
        instance = super().save(commit)
        return instance
