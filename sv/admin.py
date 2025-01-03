from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import (
    OrganismeNuisible,
    StatutReglementaire,
    Contexte,
    Departement,
    Region,
    Lieu,
    StatutEtablissement,
    PositionChaineDistribution,
    StructurePreleveuse,
    SiteInspection,
    MatricePrelevee,
    EspeceEchantillon,
    Laboratoire,
    Prelevement,
    StatutEvenement,
    FicheDetection,
    NumeroFiche,
    Etat,
    ZoneInfestee,
    FicheZoneDelimitee,
)

admin.site.site_header = "Administration de Sèves"


@admin.register(FicheDetection)
class FicheDetectionAdmin(VersionAdmin):
    autocomplete_fields = ["contacts"]


admin.site.register(OrganismeNuisible)
admin.site.register(StatutReglementaire)
admin.site.register(Contexte)
admin.site.register(Departement)
admin.site.register(Region)
admin.site.register(Lieu)
admin.site.register(StatutEtablissement)
admin.site.register(PositionChaineDistribution)
admin.site.register(StructurePreleveuse)
admin.site.register(SiteInspection)
admin.site.register(MatricePrelevee)
admin.site.register(EspeceEchantillon)
admin.site.register(Laboratoire)
admin.site.register(Prelevement)
admin.site.register(StatutEvenement)
admin.site.register(NumeroFiche)
admin.site.register(Etat)
admin.site.register(ZoneInfestee)
admin.site.register(FicheZoneDelimitee)
