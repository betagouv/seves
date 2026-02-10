from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import (
    Contexte,
    EspeceEchantillon,
    Evenement,
    FicheDetection,
    FicheZoneDelimitee,
    Laboratoire,
    Lieu,
    MatricePrelevee,
    OrganismeNuisible,
    PositionChaineDistribution,
    Prelevement,
    SiteInspection,
    StatutEtablissement,
    StatutEvenement,
    StatutReglementaire,
    StructurePreleveuse,
    VersionFicheZoneDelimitee,
    ZoneInfestee,
)

admin.site.site_header = "Administration de Sèves"


@admin.register(FicheDetection)
class FicheDetectionAdmin(VersionAdmin):
    pass


@admin.register(Evenement)
class EvenementnAdmin(VersionAdmin):
    autocomplete_fields = ["contacts"]

    def get_queryset(self, request):
        return self.model._base_manager.all()


@admin.register(VersionFicheZoneDelimitee)
class VersionFicheZoneDelimiteeAdmin(VersionAdmin):
    readonly_fields = ("fiche_zone_delimitee_data",)


admin.site.register(OrganismeNuisible)
admin.site.register(StatutReglementaire)
admin.site.register(Contexte)
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
admin.site.register(ZoneInfestee)
admin.site.register(FicheZoneDelimitee)
