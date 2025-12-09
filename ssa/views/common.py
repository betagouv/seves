from django.urls import reverse
from django.views import View

from core.mixins import WithExportHeterogeneousQuerysetMixin
from ssa.tasks import export_task
from ssa.views.mixins import WithFilteredListMixin


class CsvExportView(WithFilteredListMixin, WithExportHeterogeneousQuerysetMixin, View):
    http_method_names = ["post"]

    def get_export_task(self):
        return export_task

    def get_success_url(self):
        return reverse("ssa:evenements-liste")
