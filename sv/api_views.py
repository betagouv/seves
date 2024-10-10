from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from sv.models import EspeceEchantillon


@require_http_methods(["GET"])
def search_espece_echantillon(request):
    search_term = request.GET.get("q", "")
    if not search_term:
        return JsonResponse({"results": []})

    especes = EspeceEchantillon.objects.filter(libelle__icontains=search_term)
    results = [{"id": espece.id, "name": espece.libelle} for espece in especes]
    return JsonResponse({"results": results})
