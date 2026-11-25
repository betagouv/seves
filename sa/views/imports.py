from django.http import JsonResponse
from django.views.generic import TemplateView

from sa.forms.imports import ImportForm
from sa.import_csv import EmptyFileError, MissingColumnsError, parse_csv

EMPTY_FILE_ERROR = "Le fichier ne contient aucune ligne à importer."


class ImportView(TemplateView):
    template_name = "sa/import.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(form=ImportForm(), **kwargs)

    def post(self, request, *args, **kwargs):
        form = ImportForm(request.POST, request.FILES)
        if form.has_error("file", "empty"):
            return JsonResponse({"error": EMPTY_FILE_ERROR}, status=400)
        if not form.is_valid():
            return JsonResponse({"error": "Veuillez sélectionner un fichier au format .csv."}, status=400)

        try:
            plan = parse_csv(form.cleaned_data["file"], request.user)
        except MissingColumnsError as error:
            return JsonResponse({"error": f"Colonnes manquantes dans le fichier : {error}."}, status=400)
        except EmptyFileError:
            return JsonResponse({"error": EMPTY_FILE_ERROR}, status=400)

        if self.request.POST.get("action") == "test":
            return JsonResponse(plan.summary())

        if self.request.POST.get("action") == "create":
            csv_import = form.save(commit=False)
            csv_import.createur = request.user.agent.structure
            csv_import.nom_fichier = form.cleaned_data["file"].name
            csv_import.save()
            return JsonResponse(plan.apply(csv_import, request.user))
        raise NotImplementedError
