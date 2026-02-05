import csv
import requests
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from io import StringIO

from ssa.form_mixins import WithFreeLinksQuerysetsMixin
from ssa.models import EvenementProduit

CSV_URLS = [
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA1_ACTIV_GEN.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA1_VIAN_ONG_DOM.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA1_VIAN_COL_LAGO.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA1_VIAN_GIB_ELEV.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA1_VIAN_GIB_SAUV.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA1_VIAND_HACHE_VSM.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA4_AGSANPROBASEVDE_PRV.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA4B_AS_CE_PRODCOQUI_COV.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA4B_AS_CE_PRODPECHE_COV.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA1_LAIT.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA1_OEUF.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA1_GREN_ESCARG.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA4_AGSANGREXPR_PRV.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA4_AGR_ESVEBO_PRV.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA4_AGSANGELAT_PRV.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA4_AGSANCOLL_PRV.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA_PROD_RAFF.txt",
    "https://fichiers-publics.agriculture.gouv.fr/dgal/ListesOfficielles/SSA4_ASCCC_PRV.txt",
]


class FindNumeroAgrementView(View):
    def get(self, request):
        for url in CSV_URLS:
            csv_data = csv.reader(StringIO(requests.get(url).text))
            next(csv_data, None)

            for row in csv_data:
                if len(row) >= 3 and row[2] == self.request.GET.get("siret"):
                    return JsonResponse({"numero_agrement": row[1]})
        return JsonResponse({"error": "SIRET non trouvé"}, status=404)


class FindFreeLinksView(WithFreeLinksQuerysetsMixin, View):
    def get(self, request):
        query = self.request.GET.get("q")
        if not query or len(query) < 5:
            return JsonResponse({"error": "Le terme de recherche est trop pour une recherche"}, status=400)
        user = self.request.user
        choices = [
            ("Événement produit", self.get_queryset(EvenementProduit, user, instance=None)),
            ("Investigation de cas humain", self._get_cas_humain_queryset(user)),
            ("Enregistrement simple", self._get_evenement_simple_queryset(user)),
            ("Investigation de tiac", self._get_investigation_tiac_queryset(user)),
        ]

        parts = query.split("-")[-1].split(".")
        results = []
        for prefix, queryset in choices:
            if len(parts) == 1:
                queryset = queryset.filter(
                    Q(numero_annee__icontains=parts[0]) | Q(numero_evenement__icontains=parts[0])
                )
            if len(parts) == 2:
                queryset = queryset.filter(numero_annee__icontains=parts[0], numero_evenement__icontains=parts[1])

            if not queryset:
                continue

            content_type_id = ContentType.objects.get_for_model(queryset[0]).id
            results += [{"value": f"{content_type_id}-{e.pk}", "label": f"{prefix} : {e}"} for e in queryset]

        return JsonResponse({"results": results})
