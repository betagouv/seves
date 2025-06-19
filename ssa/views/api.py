import csv
import requests
from django.http import JsonResponse
from django.views import View
from io import StringIO

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
