
from django.views.generic.edit import FormView
from .forms import DocumentUploadForm
from django.http import HttpResponseRedirect

class DocumentUploadView(FormView):
    form_class = DocumentUploadForm

    def post(self, request, *args, **kwargs):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/success/url/')
        # TODO what to do when we have an error ?