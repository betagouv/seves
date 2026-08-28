from django.conf import settings
from django.forms import Media
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, TemplateView

from core.metabase import get_dashboard_token
from core.mixins import MediaDefiningMixin, WithExportHeterogeneousQuerysetMixin
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


class EvenementsListView(MediaDefiningMixin, WithFilteredListMixin, ListView):
    template_name = "ssa/evenements_list.html"
    model = EvenementProduit
    paginate_by = 100

    def get_media(self, **context_data) -> Media:
        return super().get_media(**context_data) + self.filter.form.media

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter
        context["total_object_count"] = self.get_raw_queryset().count()
        context["voluminous_extract_threshold"] = settings.VOLUMINOUS_EXTRACT_THRESHOLD
        context["object_list"] = [EvenementDisplay.from_evenement(evenement) for evenement in context["object_list"]]

        return context


class StatsEvenementsView(TemplateView):
    template_name = "ssa/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not settings.METABASE_SECRET_KEY:
            return context

        context["evenement_produit_token"] = get_dashboard_token(int(settings.METABASE_EVENEMENT_PRODUIT))
        context["ich_token"] = get_dashboard_token(int(settings.METABASE_EVENEMENT_ICH))
        context["investigation_tiac_token"] = get_dashboard_token(int(settings.METABASE_EVENEMENT_INVESTIGATION_TIAC))
        context["enregistrement_simple_token"] = get_dashboard_token(
            int(settings.METABASE_EVENEMENT_ENREGISTREMENT_SIMPLE)
        )
        context["METABASE_URL"] = settings.METABASE_URL
        context["title"] = "Analyse des évènements"
        return context


class StatsActiviteView(TemplateView):
    template_name = "ssa/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not settings.METABASE_SECRET_KEY:
            return context

        context["evenement_produit_token"] = get_dashboard_token(int(settings.METABASE_MESURE_ACTIVITE_PRODUIT))
        context["ich_token"] = get_dashboard_token(int(settings.METABASE_MESURE_ACTIVITE_ICH))
        context["investigation_tiac_token"] = get_dashboard_token(
            int(settings.METABASE_MESURE_ACTIVITE_INVESTIGATION_TIAC)
        )
        context["enregistrement_simple_token"] = get_dashboard_token(
            int(settings.METABASE_MESURE_ACTIVITE_ENREGISTREMENT_SIMPLE)
        )
        context["METABASE_URL"] = settings.METABASE_URL
        context["title"] = "Mesure d’activité"
        return context
