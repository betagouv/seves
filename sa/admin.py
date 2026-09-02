from django.contrib import admin
from django.contrib.gis import forms

from .models import Espece, EvenementAnimal, Laboratoire, Maladie, MethodeAnalyse


class EvenementAnimalAdminForm(forms.ModelForm):
    class Meta:
        from .models import EvenementAnimal

        model = EvenementAnimal
        fields = "__all__"
        widgets = {
            "coordinates": forms.TextInput(),
        }


@admin.register(EvenementAnimal)
class EvenementAnimalAdmin(admin.ModelAdmin):
    form = EvenementAnimalAdminForm


@admin.register(Maladie)
class MaladieAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "get_description_type_display",
        "acronym",
        "needs_arrete",
        "needs_date_nd",
        "needs_dates_desinfection",
    )


@admin.register(Laboratoire)
class LaboratoireAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "external_id",
        "code",
        "get_laboratoire_type_display",
    )


@admin.register(MethodeAnalyse)
class MethodeAnalyseAdmin(admin.ModelAdmin):
    list_display = (
        "libelle_source",
        "date_maj_source",
    )
    filter_horizontal = ("laboratoires",)


admin.site.register(Espece)
