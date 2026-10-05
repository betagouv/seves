from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.views import View

from sa.models import EvenementAnimal
from ssa.form_mixins import WithFreeLinksQuerysetsMixin


class FindFreeLinksView(WithFreeLinksQuerysetsMixin, View):
    def get(self, request):
        query = self.request.GET.get("q")
        if not query or len(query) < 3:
            return JsonResponse({"error": "Le terme de recherche est trop pour une recherche"}, status=400)
        user = self.request.user
        choices = [
            ("Événement animal", self.get_queryset(EvenementAnimal, user, instance=None)),
        ]

        parts = query.split("-")[-1].split(".")
        results = []
        for prefix, queryset in choices:
            if len(parts) == 1:
                queryset = queryset.filter(numero_evenement__icontains=parts[0])
            if len(parts) == 2:
                queryset = queryset.filter(numero_annee__endswith=parts[0], numero_evenement__startswith=parts[1])
            queryset = queryset.only("id", "numero_annee", "numero_evenement")

            if not queryset:
                continue

            content_type_id = ContentType.objects.get_for_model(queryset[0]).id
            results += [
                {"value": f"{content_type_id}-{e.pk}", "label": f"{prefix} : {e} / {e.espece.name} · {e.maladie.name}"}
                for e in queryset
            ]

        return JsonResponse({"results": results})
