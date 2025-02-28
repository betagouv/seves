import math
from collections import defaultdict
from copy import copy

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from core.fields import DSFRCheckboxSelectMultiple, DSFRRadioButton, ContactModelMultipleChoiceField
from core.models import Document, Contact, Message, Structure, Visibilite
from core.validators import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MEGABYTES
from core.widgets import RestrictedFileWidget

User = get_user_model()


class DSFRForm(forms.Form):
    input_to_class = defaultdict(lambda: "fr-input")
    input_to_class["ClearableFileInput"] = "fr-upload"
    input_to_class["Select"] = "fr-select"
    input_to_class["SelectMultiple"] = "fr-select"
    input_to_class["SelectWithAttributeField"] = "fr-select"
    input_to_class["DSFRRadioButton"] = ""
    input_to_class["DSFRCheckboxSelectMultiple"] = ""
    manual_render_fields = []

    def get_context(self):
        context = super().get_context()
        context["manual_render_fields"] = self.manual_render_fields
        return context

    def as_dsfr_div(self):
        return self.render("core/_dsfr_div.html")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        for field in self.fields:
            widget = self.fields[field].widget
            class_to_add = self.input_to_class[type(widget).__name__]
            widget.attrs["class"] = widget.attrs.get("class", "") + " " + class_to_add


class WithNextUrlMixin:
    def add_next_field(self, next):
        if next:
            self.fields["next"] = forms.CharField(widget=forms.HiddenInput())
            self.initial["next"] = next


class WithContentTypeMixin:
    def add_content_type_fields(self, obj):
        if obj:
            self.fields["content_type"].widget = forms.HiddenInput()
            self.fields["object_id"].widget = forms.HiddenInput()
            self.initial["content_type"] = ContentType.objects.get_for_model(obj)
            self.initial["object_id"] = obj.pk


class DocumentUploadForm(DSFRForm, WithNextUrlMixin, WithContentTypeMixin, forms.ModelForm):
    nom = forms.CharField(
        help_text="Nommer le document de manière claire et compréhensible pour tous", label="Intitulé du document"
    )
    document_type = forms.ChoiceField(choices=Document.TypeDocument, label="Type de document")
    description = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 30, "rows": 4}), label="Commentaire - facultatif", required=False
    )
    file = forms.FileField(label="Ajouter un document", widget=RestrictedFileWidget)

    class Meta:
        model = Document
        fields = ["nom", "document_type", "description", "file", "content_type", "object_id"]

    def __init__(self, *args, **kwargs):
        obj = kwargs.pop("obj", None)
        next = kwargs.pop("next", None)
        super().__init__(*args, **kwargs)
        self.add_content_type_fields(obj)
        self.add_next_field(next)

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file and file.size > MAX_UPLOAD_SIZE_BYTES:
            raise forms.ValidationError(f"La taille du fichier ne doit pas dépasser {MAX_UPLOAD_SIZE_MEGABYTES}Mo")
        return file


class DocumentEditForm(DSFRForm, forms.ModelForm):
    nom = forms.CharField(
        help_text="Nommer le document de manière claire et compréhensible pour tous", label="Intitulé du document"
    )
    document_type = forms.ChoiceField(choices=Document.TypeDocument, label="Type de document")
    description = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 30, "rows": 4}), label="Commentaire - facultatif", required=False
    )

    class Meta:
        model = Document
        fields = ["nom", "document_type", "description"]


class ContactAddForm(DSFRForm, forms.Form):
    fiche_id = forms.IntegerField(widget=forms.HiddenInput())
    structure = forms.ModelChoiceField(
        queryset=Structure.objects.none(),
        empty_label="Choisir dans la liste",
        label_suffix="",
    )
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    content_type_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["structure"].queryset = Structure.objects.can_be_contacted()


class ContactSelectionForm(forms.Form):
    structure = forms.ModelChoiceField(queryset=Structure.objects.all(), widget=forms.HiddenInput())
    contacts = forms.ModelMultipleChoiceField(
        queryset=Contact.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label="",
        error_messages={"required": "Veuillez sélectionner au moins un contact"},
    )
    content_type_id = forms.IntegerField(widget=forms.HiddenInput())
    fiche_id = forms.IntegerField(widget=forms.HiddenInput())
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    contacts_count_half = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        structure = kwargs.pop("structure")
        fiche_id = kwargs.pop("fiche_id")
        content_type_id = kwargs.pop("content_type_id")
        super().__init__(*args, **kwargs)
        self.fields["structure"].initial = structure
        self.fields["fiche_id"].initial = fiche_id
        self.fields["content_type_id"].initial = content_type_id
        content_type = ContentType.objects.get(pk=content_type_id).model_class()
        fiche = content_type.objects.get(pk=fiche_id)
        self.fields["contacts"].queryset = (
            Contact.objects.filter(agent__structure=structure)
            .can_be_emailed()
            .exclude(pk__in=fiche.contacts.all())
            .order_by("structure", "agent__nom")
        )
        # Calcul du nombre de contacts à afficher dans la première colonne (arrondi supérieur)
        self.fields["contacts_count_half"].initial = math.ceil(self.fields["contacts"].queryset.count() / 2)


class MessageForm(DSFRForm, WithNextUrlMixin, WithContentTypeMixin, forms.ModelForm):
    recipients = ContactModelMultipleChoiceField(queryset=Contact.objects.none(), label="Destinataires*")
    recipients_structures_only = ContactModelMultipleChoiceField(
        queryset=Contact.objects.none(), label="Destinataires*"
    )
    recipients_copy = ContactModelMultipleChoiceField(queryset=Contact.objects.none(), required=False, label="Copie")
    recipients_copy_structures_only = ContactModelMultipleChoiceField(
        queryset=Contact.objects.none(), required=False, label="Copie"
    )
    recipients_limited_recipients = forms.MultipleChoiceField(
        choices=[("mus", "MUS"), ("bsv", "BSV")],
        label="Destinataires",
        widget=DSFRCheckboxSelectMultiple(attrs={"class": "fr-checkbox-group"}),
    )
    message_type = forms.ChoiceField(choices=Message.MESSAGE_TYPE_CHOICES, widget=forms.HiddenInput)
    content = forms.CharField(label="Message", widget=forms.Textarea(attrs={"cols": 30, "rows": 10}))

    manual_render_fields = [
        "recipients_structures_only",
        "recipients_copy_structures_only",
        "recipients_limited_recipients",
    ]

    class Meta:
        model = Message
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
        ]

    def _add_files_inputs(self, data, files):
        document_types = {k: v for k, v in data.items() if k.startswith("document_type_")}
        documents = {k: v for k, v in files.items() if k.startswith("document_file_")}

        if len(document_types) != len(documents):
            raise ValidationError("Il n'y a pas le même nombre de documents et de type de documents.")

        for key, value in document_types.items():
            self.fields[key] = forms.ChoiceField(initial=value, choices=Document.TypeDocument)
            document_number = key.split("_")[-1]
            document_field = forms.FileField(initial=documents[f"document_file_{document_number}"])
            self.fields[f"document_{document_number}"] = document_field

    def _get_structures(self, obj):
        if hasattr(self, "_structures"):
            return self._structures
        self._structures = obj.contacts.structures_only().exclude(structure=self.sender.agent.structure)
        self._structures = self._structures.select_related("structure")
        return self._structures

    def _get_recipients_label(self, obj):
        structure_ids = ",".join([str(c.id) for c in self._get_structures(obj)])
        return mark_safe(
            f"Destinataires*<a href='#' class='fr-link destinataires-shortcut' data-structures='{structure_ids}'>Ajouter toutes les structures de la fiche</a>"
        )

    def _get_recipients_copy_label(self, obj):
        structure_ids = ",".join([str(c.id) for c in self._get_structures(obj)])
        return mark_safe(
            f"Copie <a href='#' class='fr-link copie-shortcut' data-structures='{structure_ids}'>Ajouter toutes les structures de la fiche</a>"
        )

    def __init__(self, *args, sender, **kwargs):
        obj = kwargs.pop("obj", None)
        self.sender = sender
        next_url = kwargs.pop("next", None)
        super().__init__(*args, **kwargs)
        queryset = Contact.objects.with_structure_and_agent().can_be_emailed().select_related("agent__structure")
        self.fields["recipients"].queryset = queryset
        self.fields["recipients_copy"].queryset = queryset

        queryset_structures = Contact.objects.structures_only().can_be_emailed().select_related("structure")
        self.fields["recipients_structures_only"].queryset = queryset_structures
        self.fields["recipients_copy_structures_only"].queryset = queryset_structures

        if self._get_structures(obj):
            self.fields["recipients"].label = self._get_recipients_label(obj)
            self.fields["recipients_structures_only"].label = self._get_recipients_label(obj)
            self.fields["recipients_copy"].label = self._get_recipients_copy_label(obj)
            self.fields["recipients_copy_structures_only"].label = self._get_recipients_copy_label(obj)

        if kwargs.get("data") and kwargs.get("files"):
            self._add_files_inputs(kwargs.get("data"), kwargs.get("files"))

        self.add_content_type_fields(obj)
        self.add_next_field(next_url)

        if kwargs.get("data"):
            message_type = kwargs.get("data")["message_type"]
            if (
                message_type in Message.TYPES_WITHOUT_RECIPIENTS
                or message_type in Message.TYPES_WITH_LIMITED_RECIPIENTS
            ):
                self.fields.pop("recipients")
                self.fields.pop("recipients_copy")
            if message_type not in Message.TYPES_WITH_LIMITED_RECIPIENTS:
                self.fields.pop("recipients_limited_recipients")

            if message_type in Message.TYPES_WITH_STRUCTURES_ONLY:
                self.fields.pop("recipients")
                self.fields.pop("recipients_copy")
            else:
                self.fields.pop("recipients_structures_only")
                self.fields.pop("recipients_copy_structures_only")

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
        if self.cleaned_data["message_type"] in Message.TYPES_WITH_STRUCTURES_ONLY:
            self.cleaned_data["recipients"] = self.cleaned_data["recipients_structures_only"]
            self.cleaned_data["recipients_copy"] = self.cleaned_data["recipients_copy_structures_only"]
        self.instance.sender = self.sender


class MessageDocumentForm(DSFRForm, forms.ModelForm):
    document_type = forms.ChoiceField(
        choices=[
            ("", ""),
        ]
        + Document.TypeDocument.choices,
        label="Type de document",
        required=False,
    )
    file = forms.FileField(
        label="Ajouter un document", required=False, widget=RestrictedFileWidget(attrs={"disabled": True})
    )

    class Meta:
        model = Document
        fields = ["document_type", "file"]


class StructureAddForm(forms.Form):
    fiche_id = forms.IntegerField(widget=forms.HiddenInput())
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    content_type_id = forms.IntegerField(widget=forms.HiddenInput())
    structure_niveau1 = forms.ChoiceField(choices=[], label="En :", widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        niveau1_choices = Structure.objects.can_be_contacted()
        niveau1_choices = niveau1_choices.values_list("niveau1", flat=True).distinct().order_by("niveau1")
        self.fields["structure_niveau1"].choices = [(niveau1, niveau1) for niveau1 in niveau1_choices]
        self.fields["structure_niveau1"].initial = niveau1_choices.first()


class StructureSelectionForm(forms.Form):
    content_type_id = forms.IntegerField(widget=forms.HiddenInput())
    fiche_id = forms.IntegerField(widget=forms.HiddenInput())
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    structure_selected = forms.CharField(widget=forms.HiddenInput())
    contacts = forms.ModelMultipleChoiceField(
        queryset=Contact.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label="",
        error_messages={"required": "Veuillez sélectionner au moins une structure"},
    )
    contacts_count_half = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        fiche_id = kwargs.pop("fiche_id")
        content_type_id = kwargs.pop("content_type_id")
        structure_selected = kwargs.pop("structure_selected")
        super().__init__(*args, **kwargs)
        self.fields["fiche_id"].initial = fiche_id
        self.fields["content_type_id"].initial = content_type_id
        self.fields["structure_selected"].initial = structure_selected
        content_type = ContentType.objects.get(pk=content_type_id).model_class()
        fiche = content_type.objects.get(pk=fiche_id)
        existing_contact = fiche.contacts.all()
        self.fields["contacts"].queryset = (
            Contact.objects.filter(structure__niveau1=structure_selected)
            .can_be_emailed()
            .exclude(pk__in=existing_contact)
            .order_by("structure", "agent__nom")
        )
        # Calcul du nombre de contacts à afficher dans la première colonne (arrondi supérieur)
        self.fields["contacts_count_half"].initial = math.ceil(self.fields["contacts"].queryset.count() / 2)


class VisibiliteUpdateBaseForm(DSFRForm):
    visibilite = forms.ChoiceField(
        label="",
        widget=DSFRRadioButton(attrs={"hint_text": {choice.value: choice.label.capitalize() for choice in Visibilite}}),
    )

    def __init__(self, *args, **kwargs):
        obj = kwargs.pop("obj", None)
        super().__init__(*args, **kwargs)
        object = obj or self.instance

        locale = (Visibilite.LOCALE, Visibilite.LOCALE.capitalize())
        limitee = (Visibilite.LIMITEE, Visibilite.LIMITEE.capitalize())
        nationale = (Visibilite.NATIONALE, Visibilite.NATIONALE.capitalize())

        self.fields["visibilite"].choices = [locale, limitee, nationale]
        self.fields["visibilite"].initial = object.visibilite
