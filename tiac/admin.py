from django.contrib import admin

from .models import AlimentSuspect, AnalyseAlimentaire, Etablissement, EvenementSimple, InvestigationTiac, RepasSuspect


class InvestigationTiacAdmin(admin.ModelAdmin):
    raw_id_fields = ("contacts",)


class EvenementSimpleAdmin(admin.ModelAdmin):
    raw_id_fields = ("contacts",)


admin.site.register(EvenementSimple, EvenementSimpleAdmin)
admin.site.register(Etablissement)
admin.site.register(InvestigationTiac, InvestigationTiacAdmin)
admin.site.register(RepasSuspect)
admin.site.register(AlimentSuspect)
admin.site.register(AnalyseAlimentaire)
