from core.models import Document
from django import forms

class DocumentUploadForm(forms.ModelForm):


    class Meta:
        model = Document
        fields = ['nom', 'file']