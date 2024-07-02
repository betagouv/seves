from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView
from .forms import (
    DocumentUploadForm,
    MessageForm,
    MessageDocumentForm,
    DocumentEditForm,
    ContactAddForm,
    ContactSelectionForm,
)
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import ngettext


from .models import Document, Message

from django.contrib.contenttypes.models import ContentType


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


class ContactAddFormView(FormView):
    template_name = "core/_contact_add_form.html"
    form_class = ContactAddForm

    def get_initial(self):
        initial = super().get_initial()
        initial["fiche_id"] = self.request.GET.get("fiche_id")
        initial["next"] = self.request.GET.get("next")
        initial["content_type_id"] = self.request.GET.get("content_type_id")
        return initial

    def form_valid(self, form):
        selection_form = ContactSelectionForm(
            structure=form.cleaned_data.get("structure"),
            fiche_id=form.cleaned_data.get("fiche_id"),
            content_type_id=form.cleaned_data.get("content_type_id"),
            initial={
                "next": form.cleaned_data.get("next"),
            },
        )
        return render(self.request, self.template_name, {"form": form, "selection_form": selection_form})


class ContactSelectionView(FormView):
    template_name = "core/_contact_add_form.html"
    form_class = ContactSelectionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = self.request.GET.get("next")
        return context

    def get_form_kwargs(self):
        kwargs = super(ContactSelectionView, self).get_form_kwargs()
        kwargs.update(
            {
                "structure": self.request.POST.get("structure", ""),
                "fiche_id": self.request.POST.get("fiche_id", ""),
                "content_type_id": self.request.POST.get("content_type_id", ""),
            }
        )
        return kwargs

    def form_valid(self, form):
        content_type = ContentType.objects.get(pk=form.cleaned_data["content_type_id"]).model_class()
        fiche = content_type.objects.get(pk=form.cleaned_data["fiche_id"])
        contacts = form.cleaned_data["contacts"]
        for contact in contacts:
            fiche.contacts.add(contact)

        message = ngettext(
            "Le contact a été ajouté avec succès.", "Les %(count)d contacts ont été ajoutés avec succès.", len(contacts)
        ) % {"count": len(contacts)}
        messages.success(self.request, message)

        redirect_url = self.request.POST.get("next")
        return HttpResponseRedirect(redirect_url)

    def form_invalid(self, form):
        add_form = ContactAddForm(
            initial={
                "structure": form.data.get("structure"),
                "fiche_id": form.data.get("fiche_id"),
                "content_type_id": form.data.get("content_type_id"),
                "next": form.data.get("next"),
            }
        )
        return render(
            self.request,
            self.template_name,
            {
                "form": add_form,
                "selection_form": form,
            },
        )


class MessageCreateView(SuccessMessageMixin, CreateView):
    model = Message
    form_class = MessageForm
    success_message = "Le message a bien été ajouté."

    def dispatch(self, request, *args, **kwargs):
        self.obj_class = ContentType.objects.get(pk=self.kwargs.get("obj_type_pk")).model_class()
        self.obj = get_object_or_404(self.obj_class, pk=self.kwargs.get("obj_pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"obj": self.obj, "next": self.obj.get_absolute_url(), "message_type": Message.MESSAGE})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["go_back_url"] = self.obj.get_absolute_url()
        context["add_document_form"] = MessageDocumentForm()
        return context

    def get_success_url(self):
        return self.obj.get_absolute_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        message = form.instance

        content_type = ContentType.objects.get_for_model(message)
        document_numbers = [
            s.replace("document_type_", "") for s in form.cleaned_data.keys() if s.startswith("document_type_")
        ]
        for i in document_numbers:
            Document.objects.create(
                file=form.cleaned_data[f"document_{i}"],
                nom=form.cleaned_data[f"document_{i}"]._name,
                document_type=form.cleaned_data[f"document_type_{i}"],
                content_type=content_type,
                object_id=message.pk,
            )
        return response


class MessageDetailsView(DetailView):
    model = Message
