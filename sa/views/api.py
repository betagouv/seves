import json

from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.views import View

from core.models import FinSuiviContact
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


class GetMassActionStatus(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON invalide"}, status=400)

        action = data.get("action")
        pks = data.get("pks")

        queryset = EvenementAnimal.objects.all().get_user_can_view(self.request.user).filter(pk__in=pks)
        if action == "fin_suivi":
            can_be_done = 0
            for evenement in queryset:
                if FinSuiviContact.can_add_fin_de_suivi(evenement, self.request.user):
                    can_be_done += 1
            return JsonResponse({"can_be_done": can_be_done})
        if action == "cloture":
            if not EvenementAnimal.can_be_cloture_by(self.request.user):
                return JsonResponse({"error": "Action non autorisée"}, status=403)
            return JsonResponse(self.get_cloture_status(queryset))

        raise NotImplementedError

    def get_cloture_status(self, queryset):
        eligibles = queryset.filter(etat=EvenementAnimal.Etat.EN_COURS)
        return {
            "can_be_done": eligibles.count(),
            "draft": queryset.filter(etat=EvenementAnimal.Etat.BROUILLON).count(),
            "already_cloture": queryset.filter(etat=EvenementAnimal.Etat.CLOTURE).count(),
            # La structure de l'agent n'est pas comptée : sa fin de suivi est ajoutée lors de la clôture
            "not_in_fin_suivi": eligibles.having_structures_not_in_fin_suivi(
                excluded_structure=self.request.user.agent.structure
            ).count(),
        }
