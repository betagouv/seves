from django.conf import settings
from django.contrib import messages
from django.views.generic.edit import FormView
from .forms import DocumentUploadForm
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme


class DocumentUploadView(FormView):
    form_class = DocumentUploadForm

    def _get_redirect(self):
        if url_has_allowed_host_and_scheme(
                url=self.request.POST.get('next'),
                allowed_hosts={self.request.get_host()},
                require_https=self.request.is_secure()
        ):
            return HttpResponseRedirect(self.request.POST.get('next'))
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)


    def post(self, request, *args, **kwargs):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Le document a été ajouté avec succés.")
            return self._get_redirect()

        messages.error(request, "Une erreur s'est produite lors de l'ajout du document")
        return self._get_redirect()

