from django.contrib import admin
from .models import EvenementProduit, Etablissement, EvenementInvestigationCasHumain

admin.site.register(EvenementProduit)
admin.site.register(EvenementInvestigationCasHumain)
admin.site.register(Etablissement)
