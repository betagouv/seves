import json

from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from core.mixins import WithExportHeterogeneousQuerysetMixin
from ssa.constants import CategorieDanger, CategorieProduit
from ssa.display import EvenementDisplay
from ssa.models import EvenementProduit
from ssa.tasks import export_task
from ssa.views.mixins import WithFilteredListMixin


class CsvExportView(WithFilteredListMixin, WithExportHeterogeneousQuerysetMixin, View):
    http_method_names = ["post"]

    def get_export_task(self):
        return export_task

    def get_success_url(self):
        return reverse("ssa:evenements-liste")


class EvenementsListView(WithFilteredListMixin, ListView):
    template_name = "ssa/evenements_list.html"
    model = EvenementProduit
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter
        context["categorie_produit_data"] = json.dumps(CategorieProduit.build_options())
        context["categorie_danger_data"] = json.dumps(CategorieDanger.build_options(sorted_results=True))

        context["total_object_count"] = self.get_raw_queryset().count()
        context["object_list"] = [EvenementDisplay.from_evenement(evenement) for evenement in context["object_list"]]

        return context
