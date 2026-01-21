import uuid
from collections import OrderedDict

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.forms import Media
from django.utils.safestring import mark_safe
from django_countries.fields import CountryField
from dsfr.forms import DsfrBaseForm

from core.constants import Domains
from core.fields import (
    AdresseLieuDitField,
    ContactModelMultipleChoiceField,
    DSFRRadioButton,
    MessageContentField,
    MessageObjectField,
    SEVESChoiceField,
)
from core.form_mixins import DSFRForm
from core.models import Contact, Departement, Document, Message, Structure, Visibilite
from core.validators import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MEGABYTES

User = get_user_model()


class BaseDocumentUploadForm(DsfrBaseForm, forms.ModelForm):
    nom = forms.CharField(
        label="Intitulé du document",
        widget=forms.TextInput(attrs={"maxlength": 256, "required": True}),
    )
    document_type = SEVESChoiceField(
        choices=Document.TypeDocument.choices,
        label="Type de document",
        widget=forms.Select(attrs={"required": True}),
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 30, "rows": 4}), label="Commentaire - facultatif", required=False
    )
    file = forms.FileField(label="Ajouter un document")

    @property
    def media(self):
        return super().media + Media(css={"all": ("core/form/document_in_message_upload.css",)})

    def __init__(self, user, related_to, allowed_document_types, *args, **kwargs):
        self.user = user
        self.related_to = related_to
        self.allowed_document_types = allowed_document_types

        super().__init__(*args, **kwargs)

        self.fields["document_type"].choices = [
            ("", settings.SELECT_EMPTY_CHOICE),
            *[(c.value, c.label) for c in self.allowed_document_types],
        ]

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file:
            return
        if file.size > MAX_UPLOAD_SIZE_BYTES:
            raise forms.ValidationError(f"La taille du fichier ne doit pas dépasser {MAX_UPLOAD_SIZE_MEGABYTES}Mo")
        if document_type := self.cleaned_data.get("document_type"):
            Document.validate_file_extention_for_document_type(file, document_type)
        return file

    def full_clean(self):
        super().full_clean()
        # Move errors related to the `file` field so they are visible on `nom` field
        for error in self.errors.pop("file", []):
            self.add_error("nom", error)

    class Meta:
        model = Document
        fields = ["id", "nom", "document_type", "description", "file"]


class DocumentUploadForm(BaseDocumentUploadForm):
    template_name = "core/form/document_upload.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["content_type"].widget = forms.HiddenInput()
        self.initial["content_type"] = ContentType.objects.get_for_model(self.related_to)
        self.fields["object_id"].widget = forms.HiddenInput()
        self.initial["object_id"] = self.related_to.pk

    def clean(self):
        self.instance.content_object = self.cleaned_data["content_type"].get_object_for_this_type(
            pk=self.cleaned_data["object_id"]
        )
        return super().clean()

    def save(self, commit=True):
        agent = self.user.agent
        self.instance.created_by = agent
        self.instance.created_by_structure = agent.structure
        return super().save(commit)

    class Meta(BaseDocumentUploadForm.Meta):
        fields = (*BaseDocumentUploadForm.Meta.fields, "content_type", "object_id")


class DocumentInMessageUploadForm(BaseDocumentUploadForm):
    template_name = "core/form/document_in_message_upload.html"

    @property
    def file_id(self):
        return "" if not self.instance else uuid.uuid4()

    def __init__(self, user, related_to, allowed_document_types, *args, **kwargs):
        self.related_to = related_to
        super().__init__(user, related_to, allowed_document_types, *args, **kwargs)
        self.instance.content_object = self.related_to

    def save(self, commit=True):
        self.instance.created_by = self.user.agent
        self.instance.created_by_structure = self.user.agent.structure
        # Force setting object_id after Message instance was saved
        self.instance.content_object = self.related_to
        return super().save(commit)

    class Meta(BaseDocumentUploadForm.Meta):
        pass


class DocumentEditForm(DSFRForm, forms.ModelForm):
    nom = forms.CharField(
        help_text="Nommer le document de manière claire et compréhensible pour tous",
        label="Intitulé du document",
        widget=forms.TextInput(attrs={"maxlength": 256}),
    )
    document_type = forms.ChoiceField(choices=Document.TypeDocument, label="Type de document")
    description = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 30, "rows": 4}), label="Commentaire - facultatif", required=False
    )

    class Meta:
        model = Document
        fields = ["nom", "document_type", "description"]


class CommonMessageMixin:
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

            if data.get(f"document_name_{document_number}"):
                document_name = forms.CharField(initial=data.get(f"document_name_{document_number}"))
                self.fields[f"document_name_{document_number}"] = document_name

            if data.get(f"document_comment_{document_number}"):
                document_comment = forms.CharField(initial=data.get(f"document_comment_{document_number}"))
                self.fields[f"document_comment_{document_number}"] = document_comment

    def _get_fin_suivi_emails(self, obj):
        if hasattr(self, "_fin_suivi_emails"):
            return self._fin_suivi_emails

        self._fin_suivi_emails = Contact.objects.get_emails_in_fin_de_suivi_for_object(obj)
        return self._fin_suivi_emails

    def _get_structures(self, obj):
        if hasattr(self, "_structures"):
            return self._structures
        self._structures = (
            obj.contacts.structures_only()
            .exclude(structure=self.sender.agent.structure)
            .exclude(email__in=self._get_fin_suivi_emails(obj))
        )
        self._structures = self._structures.select_related("structure")
        return self._structures

    def _get_contacts(self, obj):
        if hasattr(self, "_contacts"):
            return self._contacts
        self._contacts = (
            obj.contacts.exclude(structure=self.sender.agent.structure)
            .exclude(agent=self.sender.agent)
            .exclude(email__in=self._get_fin_suivi_emails(obj))
        )
        self._contacts = self._contacts.select_related("agent__structure")
        return self._contacts

    def _build_label_with_shortcuts(self, label_text, obj, with_contacts=False, prefix="destinataires"):
        structure_ids = ",".join([str(c.id) for c in self._get_structures(obj)])
        html_parts = [f"{label_text}"]
        if with_contacts:
            contact_ids = ",".join([str(c.id) for c in self._get_contacts(obj)])
            html_parts.append(
                f"<p class='fr-mb-1v'>"
                f"<a href='#' data-action='message-form#onShortcut{prefix.title()}:stop:prevent' class='fr-link {prefix}-contacts-shortcut' "
                f"data-contacts='{contact_ids}'>Ajouter tous les contacts de la fiche</a></p>"
            )
        html_parts.append(
            f"<p class='fr-mb-2v'>"
            f"<a href='#' data-action='message-form#onShortcut{prefix.title()}:stop:prevent' class='fr-link {prefix}-shortcut' "
            f"data-structures='{structure_ids}' data-contacts='{structure_ids}'>Ajouter seulement les structures de la fiche</a></p>"
        )
        return mark_safe("\n".join(html_parts))

    def _get_recipients_label(self, obj):
        return self._build_label_with_shortcuts(
            mark_safe('<span class="label-marked">Destinataires</span>'), obj, with_contacts=True
        )

    def _get_recipients_copy_label(self, obj):
        return self._build_label_with_shortcuts("Copie", obj, with_contacts=True, prefix="copie")

    def _get_recipients_structures_only_label(self, obj):
        return self._build_label_with_shortcuts(mark_safe('<span class="label-marked">Destinataires</span>'), obj)

    def _get_recipients_copy_structures_only_label(self, obj):
        return self._build_label_with_shortcuts("Copie", obj, prefix="copie")

    def _add_related_objects(self):
        self.instance.status = self.status
        self.instance.sender = self.sender
        self.instance.sender_structure = self.sender.agent.structure
        self.instance.object_id = self.obj.id
        self.instance.content_type_id = ContentType.objects.get_for_model(self.obj).pk

    def clean(self):
        super().clean()
        self.status = self.data.get("action", self.data.get("status"))
        if self.status not in Message.Status:
            raise NotImplementedError

    def handle_files(self, kwargs):
        if kwargs.get("data") and kwargs.get("files"):
            self._add_files_inputs(kwargs.get("data"), kwargs.get("files"))

    def set_labels(self):
        for field in self:
            field.label = self.fields[field.name].label

    def _add_object_field(self, obj, message_type):
        field = MessageObjectField(obj, Message.get_email_type_display_from_value(message_type), self.sender)
        new_field = ("message_object", field)
        fields = list(self.fields.items())
        index = next(i for i, (name, _) in enumerate(fields) if name == "title")
        fields.insert(index, new_field)
        self.fields = OrderedDict(fields)


class BasicMessageForm(DsfrBaseForm, CommonMessageMixin, forms.ModelForm):
    page_title = "Nouveau message"
    recipients = ContactModelMultipleChoiceField(queryset=Contact.objects.none(), label="Destinataires")
    recipients_copy = ContactModelMultipleChoiceField(queryset=Contact.objects.none(), required=False, label="Copie")
    message_object = None
    content = MessageContentField()

    def __init__(self, *args, sender, **kwargs):
        obj = kwargs.pop("obj", None)
        self.obj = obj
        self.sender = sender
        super().__init__(*args, **kwargs)
        self._add_object_field(obj, Message.MESSAGE)
        queryset = Contact.objects.with_structure_and_agent().can_be_emailed().select_related("agent__structure")

        if hasattr(obj, "limit_contacts_to_user_from_app"):
            queryset = queryset.for_apps(obj.limit_contacts_to_user_from_app).distinct()

        self.fields["recipients"].queryset = queryset
        self.fields["recipients_copy"].queryset = queryset

        if self._get_structures(obj):
            self.fields["recipients"].label = self._get_recipients_label(obj)
            self.fields["recipients_copy"].label = self._get_recipients_copy_label(obj)

        self.handle_files(kwargs)
        self.set_labels()

    def clean(self):
        super().clean()
        self.instance.message_type = Message.MESSAGE
        self._add_related_objects()

    class Meta:
        model = Message
        fields = [
            "recipients",
            "recipients_copy",
            "title",
            "content",
        ]


class NoteForm(DsfrBaseForm, CommonMessageMixin, forms.ModelForm):
    page_title = "Nouvelle note"
    content = MessageContentField()

    def __init__(self, *args, sender, **kwargs):
        obj = kwargs.pop("obj", None)
        self.obj = obj
        self.sender = sender
        super().__init__(*args, **kwargs)
        self._add_object_field(obj, Message.NOTE)

        self.handle_files(kwargs)
        self.set_labels()

    def clean(self):
        super().clean()
        self.instance.message_type = Message.NOTE
        self._add_related_objects()

    class Meta:
        model = Message
        fields = ["title", "content"]


class PointDeSituationForm(DsfrBaseForm, CommonMessageMixin, forms.ModelForm):
    page_title = "Nouveau point de situation"
    help_text = "Ce point de situation sera envoyé à tous les agents et les structures en contact de cet évènement "
    content = MessageContentField()

    def __init__(self, *args, sender, **kwargs):
        obj = kwargs.pop("obj", None)
        self.obj = obj
        self.sender = sender
        super().__init__(*args, **kwargs)
        self._add_object_field(obj, Message.POINT_DE_SITUATION)

        self.handle_files(kwargs)
        self.set_labels()

    def clean(self):
        super().clean()
        self.instance.message_type = Message.POINT_DE_SITUATION
        self._add_related_objects()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            instance.recipients.set(self.obj.contacts.all())
        return instance

    class Meta:
        model = Message
        fields = ["title", "content"]


class DemandeInterventionForm(DsfrBaseForm, CommonMessageMixin, forms.ModelForm):
    page_title = "Nouvelle demande d'intervention"
    recipients = ContactModelMultipleChoiceField(queryset=Contact.objects.none(), label="Destinataires")
    recipients_copy = ContactModelMultipleChoiceField(queryset=Contact.objects.none(), required=False, label="Copie")
    content = MessageContentField()

    def __init__(self, *args, sender, **kwargs):
        obj = kwargs.pop("obj", None)
        self.obj = obj
        self.sender = sender
        super().__init__(*args, **kwargs)
        self._add_object_field(obj, Message.DEMANDE_INTERVENTION)

        queryset_structures = Contact.objects.structures_only().can_be_emailed().select_related("structure")
        if hasattr(obj, "limit_contacts_to_user_from_app"):
            queryset_structures = queryset_structures.for_apps(obj.limit_contacts_to_user_from_app).distinct()

        self.fields["recipients"].queryset = queryset_structures
        self.fields["recipients_copy"].queryset = queryset_structures

        if self._get_structures(obj):
            self.fields["recipients"].label = self._get_recipients_structures_only_label(obj)
            self.fields["recipients_copy"].label = self._get_recipients_copy_structures_only_label(obj)

        self.handle_files(kwargs)
        self.set_labels()

    def clean(self):
        super().clean()
        self.instance.message_type = Message.DEMANDE_INTERVENTION
        self._add_related_objects()

    class Meta:
        model = Message
        fields = [
            "recipients",
            "recipients_copy",
            "title",
            "content",
        ]


class BaseCompteRenduDemandeInterventionForm(DsfrBaseForm, CommonMessageMixin, forms.ModelForm):
    page_title = "Nouveau compte rendu sur demande d'intervention"
    recipients = ContactModelMultipleChoiceField(queryset=Contact.objects.none(), label="Destinataires")
    content = MessageContentField()

    def __init__(self, *args, sender, **kwargs):
        obj = kwargs.pop("obj", None)
        self.obj = obj
        self.sender = sender
        super().__init__(*args, **kwargs)
        self._add_object_field(obj, Message.COMPTE_RENDU)

        self.handle_files(kwargs)
        self.set_labels()

    def clean(self):
        super().clean()
        self.instance.message_type = Message.COMPTE_RENDU
        self._add_related_objects()

    class Meta:
        model = Message
        fields = [
            "recipients",
            "title",
            "content",
        ]


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


class StructureAddForm(DSFRForm):
    content_id = forms.IntegerField(widget=forms.HiddenInput())
    content_type_id = forms.IntegerField(widget=forms.HiddenInput())
    contacts_structures = forms.ModelMultipleChoiceField(
        queryset=Contact.objects.none(),
        widget=forms.SelectMultiple(),
        label="Ajouter une structure",
        help_text="Saisissez quelques caractères (nom, département…) pour voir des suggestions",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        obj = kwargs.pop("obj")
        super().__init__(*args, **kwargs)
        needed_group = Domains.group_for_value(obj._meta.app_label)
        queryset = (
            Contact.objects.structures_only()
            .filter(structure__in=Structure.objects.can_be_contacted_and_agent_has_group(needed_group))
            .order_by("structure__libelle")
            .select_related("structure")
        )
        if obj:
            queryset = queryset.exclude(id__in=obj.contacts.values_list("id", flat=True))
        self.fields["contacts_structures"].queryset = queryset


class AgentAddForm(DSFRForm):
    content_id = forms.IntegerField(widget=forms.HiddenInput())
    content_type_id = forms.IntegerField(widget=forms.HiddenInput())
    contacts_agents = ContactModelMultipleChoiceField(
        queryset=Contact.objects.none(),
        label="Ajouter un agent",
        help_text="Saisissez quelques caractères (nom, prénom…) pour voir des suggestions",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        obj = kwargs.pop("obj")
        super().__init__(*args, **kwargs)
        needed_group = Domains.group_for_value(obj._meta.app_label)
        queryset = (
            Contact.objects.can_be_emailed()
            .agents_with_group(needed_group)
            .select_related("agent", "agent__structure")
            .order_by("agent__structure__libelle", "agent__nom", "agent__prenom")
        )
        if obj:
            queryset = queryset.exclude(id__in=obj.contacts.values_list("id", flat=True))
        self.fields["contacts_agents"].queryset = queryset


class BaseEtablissementForm(forms.ModelForm):
    siret = forms.CharField(
        required=False,
        max_length=14,
        widget=forms.HiddenInput,
    )
    numero_agrement = forms.CharField(
        required=False,
        label="Numéro d'agrément",
        widget=forms.TextInput(attrs={"pattern": r"^\d{2,3}\.\d{2,3}\.\d{2,3}$", "placeholder": "00(0).00(0).00(0)"}),
    )
    autre_identifiant = forms.CharField(required=False)
    code_insee = forms.CharField(widget=forms.HiddenInput(), required=False)
    adresse_lieu_dit = AdresseLieuDitField(choices=[], required=False)
    pays = CountryField(blank=True).formfield(label="Pays", widget=forms.Select(attrs={"class": "fr-select"}))
    departement = forms.ModelChoiceField(
        queryset=Departement.objects.order_by("numero").all(),
        to_field_name="numero",
        required=False,
        label="Département",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields["pays"].label_suffix = ""

        if not self.is_bound and self.instance and self.instance.pk and self.instance.adresse_lieu_dit:
            self.fields["adresse_lieu_dit"].choices = [(self.instance.adresse_lieu_dit, self.instance.adresse_lieu_dit)]

        departement_obj = self.instance.departement
        if departement_obj:
            self.initial["departement"] = departement_obj.numero
