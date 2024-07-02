from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from core.models import Document, Contact, Message
from django import forms
from collections import defaultdict


class DSFRForm(forms.BaseForm):
    input_to_class = defaultdict(lambda: "fr-input")
    input_to_class["ClearableFileInput"] = "fr-upload"
    input_to_class["Select"] = "fr-select"

    def as_dsfr_div(self):
        return self.render("core/_dsfr_div.html")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            widget = self.fields[field].widget
            class_to_add = self.input_to_class[type(widget).__name__]
            widget.attrs["class"] = widget.attrs.get("class", "") + class_to_add


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
    document_type = forms.ChoiceField(choices=Document.DOCUMENT_TYPE_CHOICES, label="Type de document")
    description = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 30, "rows": 4}), label="Commentaire - facultatif", required=False
    )
    file = forms.FileField(label="Ajouter un Document")

    class Meta:
        model = Document
        fields = ["nom", "document_type", "description", "file", "content_type", "object_id"]

    def __init__(self, *args, **kwargs):
        obj = kwargs.pop("obj", None)
        next = kwargs.pop("next", None)
        super().__init__(*args, **kwargs)
        self.add_content_type_fields(obj)
        self.add_next_field(next)


class DocumentEditForm(DSFRForm, forms.ModelForm):
    nom = forms.CharField(
        help_text="Nommer le document de manière claire et compréhensible pour tous", label="Intitulé du document"
    )
    document_type = forms.ChoiceField(choices=Document.DOCUMENT_TYPE_CHOICES, label="Type de document")
    description = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 30, "rows": 4}), label="Commentaire - facultatif", required=False
    )

    class Meta:
        model = Document
        fields = ["nom", "document_type", "description"]


class ContactAddForm(DSFRForm, forms.Form):
    fiche_id = forms.IntegerField(widget=forms.HiddenInput())
    structure = forms.ChoiceField(
        label_suffix="",
        widget=forms.Select(attrs={"autocomplete": "off"}),
    )
    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    content_type_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["structure"].choices = [("", "Choisir dans la liste")] + [
            (structure, structure) for structure in Contact.objects.values_list("structure", flat=True).distinct()
        ]


class ContactSelectionForm(forms.Form):
    structure = forms.CharField(widget=forms.HiddenInput())
    contacts = forms.ModelMultipleChoiceField(
        queryset=Contact.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label="",
        error_messages={"required": "Veuillez sélectionner au moins un contact"},
    )
    content_type_id = forms.IntegerField(widget=forms.HiddenInput())
    fiche_id = forms.IntegerField(widget=forms.HiddenInput())
    next = forms.CharField(widget=forms.HiddenInput(), required=False)

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
        # Obtention des contacts déjà liés à la fiche
        existing_contacts = fiche.contacts.all()
        # Filtrage pour exclure les contacts déjà associés à la fiche
        self.fields["contacts"].queryset = (
            Contact.objects.filter(structure__icontains=structure)
            .exclude(pk__in=existing_contacts)
            .order_by("structure", "nom")
        )


class MessageForm(DSFRForm, WithNextUrlMixin, WithContentTypeMixin, forms.ModelForm):
    message_type = forms.ChoiceField(choices=Message.MESSAGE_TYPE_CHOICES, widget=forms.HiddenInput)
    content = forms.CharField(label="Message", widget=forms.Textarea(attrs={"cols": 30, "rows": 4}))

    class Meta:
        model = Message
        fields = ["message_type", "title", "content", "content_type", "object_id"]

    def _add_files_inputs(self, data, files):
        document_types = {k: v for k, v in data.items() if k.startswith("document_type_")}
        documents = {k: v for k, v in files.items() if k.startswith("document_file_")}

        if len(document_types) != len(documents):
            raise ValidationError("Il n'y a pas le même nombre de documents et de type de documents.")

        for key, value in document_types.items():
            self.fields[key] = forms.ChoiceField(initial=value, choices=Document.DOCUMENT_TYPE_CHOICES)
            document_number = key.split("_")[-1]
            document_field = forms.FileField(initial=documents[f"document_file_{document_number}"])
            self.fields[f"document_{document_number}"] = document_field

    def __init__(self, *args, message_type, **kwargs):
        obj = kwargs.pop("obj", None)
        next_url = kwargs.pop("next", None)
        super().__init__(*args, **kwargs)

        if kwargs.get("data") and kwargs.get("files"):
            self._add_files_inputs(kwargs.get("data"), kwargs.get("files"))

        self.add_content_type_fields(obj)
        self.add_next_field(next_url)
        self.initial["message_type"] = message_type


class MessageDocumentForm(DSFRForm, forms.ModelForm):
    document_type = forms.ChoiceField(
        choices=(("", ""),) + Document.DOCUMENT_TYPE_CHOICES, label="Type de document", required=False
    )
    file = forms.FileField(
        label="Ajouter un Document", required=False, widget=forms.FileInput(attrs={"disabled": True})
    )

    class Meta:
        model = Document
        fields = ["document_type", "file"]
