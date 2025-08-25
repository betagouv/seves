from django import forms
from django.forms import Media
from django.utils import timezone
from dsfr.forms import DsfrBaseForm

from core.fields import SEVESChoiceField, MultiModelChoiceField, ContactModelMultipleChoiceField
from core.form_mixins import WithFreeLinksMixin, js_module
from core.forms import BaseMessageForm
from core.models import Contact, Message
from ssa.models import EvenementProduit
from tiac.constants import EvenementOrigin, EvenementFollowUp, ModaliteDeclarationEvenement
from tiac.models import EvenementSimple


class EvenementSimpleForm(DsfrBaseForm, WithFreeLinksMixin, forms.ModelForm):
    template_name = "tiac/forms/evenement_simple.html"

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
        choices=EvenementFollowUp.choices, widget=forms.RadioSelect, label="Suite donné par la DD", required=True
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
                ("Évenement simple", queryset),
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
