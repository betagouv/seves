from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from .forms import DocumentUploadForm, DocumentEditForm
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Document


class DocumentUploadView(FormView):
    form_class = DocumentUploadForm

    def _get_redirect(self):
        if url_has_allowed_host_and_scheme(
            url=self.request.POST.get("next"),
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return HttpResponseRedirect(self.request.POST.get("next"))
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

    def post(self, request, *args, **kwargs):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Le document a été ajouté avec succès.")
            return self._get_redirect()

        messages.error(request, "Une erreur s'est produite lors de l'ajout du document")
        return self._get_redirect()


class DocumentDeleteView(View):
    def post(self, request, *args, **kwargs):
        document = get_object_or_404(Document, pk=kwargs.get("pk"))
        document.is_deleted = True
        document.save()
        messages.success(request, "Le document a été marqué comme supprimé.")
        return HttpResponseRedirect(request.POST.get("next"))


class DocumentUpdateView(SuccessMessageMixin, UpdateView):
    model = Document
    success_message = "Le document a bien été mis à jour."
    form_class = DocumentEditForm
    http_method_names = ["post"]

    def get_success_url(self):
        return self.request.POST.get("next")
