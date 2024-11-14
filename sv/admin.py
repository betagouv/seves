from django.contrib import admin
from .models import (
    OrganismeNuisible,
    StatutReglementaire,
    Contexte,
    Departement,
    Region,
    Lieu,
    StatutEtablissement,
    PositionChaineDistribution,
    StructurePreleveur,
    SiteInspection,
    MatricePrelevee,
    EspeceEchantillon,
    LaboratoireAgree,
    LaboratoireConfirmationOfficielle,
    Prelevement,
    StatutEvenement,
    FicheDetection,
    NumeroFiche,
    Etat,
    ZoneInfestee,
    FicheZoneDelimitee,
)

admin.site.site_header = "Administration de Sèves"

admin.site.register(OrganismeNuisible)
admin.site.register(StatutReglementaire)
admin.site.register(Contexte)
admin.site.register(Departement)
admin.site.register(Region)
admin.site.register(Lieu)
admin.site.register(StatutEtablissement)
admin.site.register(PositionChaineDistribution)
admin.site.register(StructurePreleveur)
admin.site.register(SiteInspection)
admin.site.register(MatricePrelevee)
admin.site.register(EspeceEchantillon)
admin.site.register(LaboratoireAgree)
admin.site.register(LaboratoireConfirmationOfficielle)
admin.site.register(Prelevement)
admin.site.register(StatutEvenement)
admin.site.register(FicheDetection)
admin.site.register(NumeroFiche)
admin.site.register(Etat)
admin.site.register(ZoneInfestee)
admin.site.register(FicheZoneDelimitee)
