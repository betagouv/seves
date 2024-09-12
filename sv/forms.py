from core.forms import DSFRForm, WithNextUrlMixin

from django.contrib.contenttypes.models import ContentType

from core.fields import MultiModelChoiceField
from django import forms

from core.models import LienLibre
from sv.models import FicheDetection


class FreeLinkForm(DSFRForm, WithNextUrlMixin, forms.ModelForm):
    object_id_1 = forms.IntegerField(widget=forms.HiddenInput())
    content_type_1 = forms.ModelChoiceField(widget=forms.HiddenInput(), queryset=ContentType.objects.all())

    class Meta:
        fields = ["object_id_1", "content_type_1"]
        model = LienLibre

    def __init__(self, *args, **kwargs):
        object_id_1 = kwargs.pop("object_id_1", None)
        content_type_1 = kwargs.pop("content_type_1", None)
        next = kwargs.pop("next", None)
        super().__init__(*args, **kwargs)
        self.fields["object_choice"] = MultiModelChoiceField(
            label="Sélectioner un objet",
            model_choices=[("FicheDetection", FicheDetection.objects.select_related("numero"))],
        )
        self.add_next_field(next)
        self.fields["object_id_1"].initial = object_id_1
        self.fields["content_type_1"].initial = content_type_1

    def clean(self):
        super().clean()
        obj = self.cleaned_data["object_choice"]
        self.instance.content_type_2 = ContentType.objects.get_for_model(obj)
        self.instance.object_id_2 = obj.id