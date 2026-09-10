from django.contrib import admin
from django.contrib.gis import forms

from .models import Analyse, Espece, EspeceConcernee, EvenementAnimal, Laboratoire, Maladie, MethodeAnalyse


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
    list_display = ("libelle",)
    filter_horizontal = ("laboratoires",)


@admin.register(Analyse)
class AnalyseAdmin(admin.ModelAdmin):
    list_display = (
        "evenement",
        "maladie",
        "laboratoire",
        "methode",
        "get_resultat_display",
        "date_prelevement",
    )


@admin.register(EspeceConcernee)
class EspeceConcerneeAdmin(admin.ModelAdmin):
    pass


admin.site.register(Espece)
