from django.contrib import admin

from .models import Etablissement, EvenementInvestigationCasHumain, EvenementProduit

admin.site.register(EvenementProduit)
admin.site.register(EvenementInvestigationCasHumain)
admin.site.register(Etablissement)
