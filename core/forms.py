from django.contrib.contenttypes.models import ContentType

from core.models import Document
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



class DocumentUploadForm(DSFRForm, forms.ModelForm):
    nom = forms.CharField(help_text="Nommer le document de manière claire et compréhensible pour tous", label="Intitulé du document")
    document_type = forms.ChoiceField(choices=Document.DOCUMENT_TYPE_CHOICES, label="Type de document")
    description = forms.CharField(widget=forms.Textarea(attrs={"cols": 30, "rows": 4}), label="Description - facultatif", required=False)
    file = forms.FileField(label="Ajouter un Document", help_text="Lorem ipsum dolor sit amet, consectetur adipiscing")

    class Meta:
        model = Document
        fields = ['nom', 'document_type', 'description', 'file', 'content_type', 'object_id']

    def __init__(self, *args, **kwargs):
        obj = kwargs.pop('obj', None)
        next = kwargs.pop('next', None)
        super().__init__(*args, **kwargs)
        if obj:
            self.fields['content_type'].widget = forms.HiddenInput()
            self.fields['object_id'].widget = forms.HiddenInput()
            self.initial['content_type'] = ContentType.objects.get_for_model(obj)
            self.initial['object_id'] = obj.pk
        if next:
            self.fields['next'] = forms.CharField(widget=forms.HiddenInput())
            self.initial['next'] = next
