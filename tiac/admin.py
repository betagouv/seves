from django.contrib import admin
from .models import EvenementSimple, Etablissement, InvestigationTiac, RepasSuspect, AlimentSuspect, AnalyseAlimentaire

admin.site.register(EvenementSimple)
admin.site.register(Etablissement)
admin.site.register(InvestigationTiac)
admin.site.register(RepasSuspect)
admin.site.register(AlimentSuspect)
admin.site.register(AnalyseAlimentaire)
