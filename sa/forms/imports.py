from django import forms

from sa.models import Import


class ImportForm(forms.ModelForm):
    class Meta:
        model = Import
        fields = ("file",)
        widgets = {
            "file": forms.FileInput(
                attrs={
                    "accept": ".csv",
                    "class": "fr-sr-only",
                    "id": "filechooser-btn",
                    "data-action": "import#onFileSelect",
                    "data-import-target": "file",
                    "data-testid": "import-filechooser",
                }
            )
        }
