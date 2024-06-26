from django.contrib.contenttypes.models import ContentType

from core.models import Document
from django import forms

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['nom', 'file', 'content_type', 'object_id']

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