import logging

from django.http import JsonResponse
from django.views.generic import TemplateView

from sa.forms.imports import ImportForm
from sa.import_csv import MissingColumnsError, create_from_row, parse_csv

logger = logging.getLogger(__name__)


class ImportView(TemplateView):
    template_name = "sa/import.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(form=ImportForm(), **kwargs)

    def post(self, request, *args, **kwargs):
        form = ImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return JsonResponse({"error": "Veuillez sélectionner un fichier au format .csv."}, status=400)

        try:
            rows, ignored = parse_csv(form.cleaned_data["file"])
        except MissingColumnsError as error:
            return JsonResponse({"error": f"Colonnes manquantes dans le fichier : {error}."}, status=400)

        if self.request.POST.get("action") == "test":
            return JsonResponse({"eligible": len(rows), "ignored": ignored})

        if self.request.POST.get("action") == "create":
            csv_import = form.save(commit=False)
            csv_import.createur = request.user.agent.structure
            csv_import.save()
            done = 0
            errors = 0
            for row in rows:
                try:
                    create_from_row(row, self.request.user)
                    done += 1
                except Exception as e:
                    logger.info(f"Could not import: {e}")
                    errors += 1
            return JsonResponse({"done": done, "errors": errors})
        raise NotImplementedError
