from django.contrib import admin
from django.contrib.gis import forms

from .models import Espece, EvenementAnimal, Maladie


class EvenementAnimalAdminForm(forms.ModelForm):
    class Meta:
        model = EvenementAnimal
        fields = "__all__"
        widgets = {
            "coordinates": forms.TextInput(),
        }


@admin.register(EvenementAnimal)
class EvenementAnimalAdmin(admin.ModelAdmin):
    form = EvenementAnimalAdminForm


admin.site.register(Maladie)
admin.site.register(Espece)
