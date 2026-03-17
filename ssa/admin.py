from django.contrib import admin

from .models import Etablissement, EvenementInvestigationCasHumain, EvenementProduit


class EvenementProduitAdmin(admin.ModelAdmin):
    raw_id_fields = ("contacts",)


class EvenementInvestigationCasHumainAdmin(admin.ModelAdmin):
    raw_id_fields = ("contacts",)


admin.site.register(EvenementProduit, EvenementProduitAdmin)
admin.site.register(EvenementInvestigationCasHumain, EvenementInvestigationCasHumainAdmin)
admin.site.register(Etablissement)
