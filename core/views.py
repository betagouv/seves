from django.contrib import messages
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
    StructureAddForm,
    StructureSelectionForm,
)
from django.http import HttpResponseRedirect
from django.utils.translation import ngettext

from .mixins import PreventActionIfVisibiliteBrouillonMixin
from .notifications import notify_message

from .models import Document, Message, Contact, FinSuiviContact

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied

from .redirect import safe_redirect


class DocumentUploadView(PreventActionIfVisibiliteBrouillonMixin, FormView):
    form_class = DocumentUploadForm

    def get_fiche_object(self):
        content_type = ContentType.objects.get(id=self.request.POST.get("content_type"))
        ModelClass = content_type.model_class()
        return get_object_or_404(ModelClass, pk=self.request.POST.get("object_id"))

    def post(self, request, *args, **kwargs):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            agent = request.user.agent
            document.created_by = agent
            document.created_by_structure = agent.structure
            document.save()
            messages.success(request, "Le document a été ajouté avec succès.", extra_tags="core documents")
            return safe_redirect(self.request.POST.get("next") + "#tabpanel-documents-panel")

        messages.error(request, "Une erreur s'est produite lors de l'ajout du document")
        return safe_redirect(self.request.POST.get("next") + "#tabpanel-documents-panel")


class DocumentDeleteView(PreventActionIfVisibiliteBrouillonMixin, View):
    def get_fiche_object(self):
        self.document = get_object_or_404(Document, pk=self.kwargs.get("pk"))
        return self.document.content_object

    def post(self, request, *args, **kwargs):
        self.document.is_deleted = True
        self.document.deleted_by = self.request.user.agent
        self.document.save()
        messages.success(request, "Le document a été marqué comme supprimé.", extra_tags="core documents")
        return safe_redirect(request.POST.get("next") + "#tabpanel-documents-panel")


class DocumentUpdateView(PreventActionIfVisibiliteBrouillonMixin, UpdateView):
    model = Document
    form_class = DocumentEditForm
    http_method_names = ["post"]

    def get_fiche_object(self):
        self.document = get_object_or_404(Document, pk=self.kwargs.get("pk"))
        return self.document.content_object

    def get_success_url(self):
        return self.request.POST.get("next") + "#tabpanel-documents-panel"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Le document a bien été mis à jour.", extra_tags="core documents")
        return response


class ContactAddFormView(PreventActionIfVisibiliteBrouillonMixin, FormView):
    template_name = "core/_contact_add_form.html"
    form_class = ContactAddForm

    def get_fiche_object(self):
        content_type_id = self.request.GET.get("content_type_id") or self.request.POST.get("content_type_id")
        fiche_id = self.request.GET.get("fiche_id") or self.request.POST.get("fiche_id")
        content_type = ContentType.objects.get(pk=content_type_id)
        ModelClass = content_type.model_class()
        return get_object_or_404(ModelClass, pk=fiche_id)

    def get_initial(self):
        initial = super().get_initial()
        initial["fiche_id"] = self.request.GET.get("fiche_id")
        initial["next"] = self.request.GET.get("next")
        initial["content_type_id"] = self.request.GET.get("content_type_id")
        initial["structure"] = self.request.user.agent.structure
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


class ContactSelectionView(PreventActionIfVisibiliteBrouillonMixin, FormView):
    template_name = "core/_contact_add_form.html"
    form_class = ContactSelectionForm

    def get_fiche_object(self):
        content_type_id = self.request.POST.get("content_type_id")
        fiche_id = self.request.POST.get("fiche_id")
        content_type = ContentType.objects.get(pk=content_type_id)
        ModelClass = content_type.model_class()
        return get_object_or_404(ModelClass, pk=fiche_id)

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
        messages.success(self.request, message, extra_tags="core contacts")

        return safe_redirect(self.request.POST.get("next") + "#tabpanel-contacts-panel")

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


class ContactDeleteView(PreventActionIfVisibiliteBrouillonMixin, View):
    def get_fiche_object(self):
        content_type = ContentType.objects.get(id=self.request.POST.get("content_type_pk"))
        ModelClass = content_type.model_class()
        self.fiche = get_object_or_404(ModelClass, pk=self.request.POST.get("fiche_pk"))
        return self.fiche

    def post(self, request, *args, **kwargs):
        contact = Contact.objects.get(pk=self.request.POST.get("pk"))
        self.fiche.contacts.remove(contact)
        messages.success(request, "Le contact a bien été supprimé de la fiche.", extra_tags="core contacts")
        return safe_redirect(request.POST.get("next") + "#tabpanel-contacts-panel")


class MessageCreateView(PreventActionIfVisibiliteBrouillonMixin, CreateView):
    model = Message
    form_class = MessageForm

    def dispatch(self, request, *args, **kwargs):
        self.message_type = self.kwargs.get("message_type")
        self.obj_class = ContentType.objects.get(pk=self.kwargs.get("obj_type_pk")).model_class()
        self.obj = get_object_or_404(self.obj_class, pk=self.kwargs.get("obj_pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_fiche_object(self):
        return self.obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "obj": self.obj,
                "next": self.obj.get_absolute_url(),
                "message_type": self.message_type,
                "sender": self.request.user,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["go_back_url"] = self.obj.get_absolute_url()
        context["add_document_form"] = MessageDocumentForm()
        context["message_type"] = self.message_type
        context["feminize"] = self.message_type in Message.TYPES_TO_FEMINIZE
        return context

    def get_success_url(self):
        return self.obj.get_absolute_url() + "#tabpanel-messages-panel"

    def _add_contacts_to_object(self, message):
        for contact in message.recipients.all().union(message.recipients_copy.all()):
            if contact not in self.obj.contacts.all():
                self.obj.contacts.add(contact)

    def _create_documents(self, form):
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
                created_by=self.request.user.agent,
                created_by_structure=self.request.user.agent.structure,
            )

    def _mark_contact_as_fin_suivi(self, form):
        message_type = form.cleaned_data.get("message_type")
        if message_type == Message.FIN_SUIVI:
            content_type = form.cleaned_data.get("content_type")
            object_id = form.cleaned_data.get("object_id")

            fin_suivi_contact = FinSuiviContact(
                content_type=content_type,
                object_id=object_id,
                contact=Contact.objects.get(structure=self.request.user.agent.structure),
            )
            fin_suivi_contact.full_clean()
            fin_suivi_contact.save()

    def form_valid(self, form):
        try:
            self._mark_contact_as_fin_suivi(form)
        except ValidationError as e:
            for message in e.messages:
                messages.error(self.request, message)
            return HttpResponseRedirect(self.obj.get_absolute_url())
        response = super().form_valid(form)
        self._add_contacts_to_object(form.instance)
        self._create_documents(form)
        notify_message(form.instance)
        messages.success(self.request, "Le message a bien été ajouté.", extra_tags="core messages")
        return response


class MessageDetailsView(PreventActionIfVisibiliteBrouillonMixin, DetailView):
    model = Message

    def get_fiche_object(self):
        message = get_object_or_404(Message, pk=self.kwargs.get("pk"))
        fiche = message.content_object
        return fiche


class StructureAddFormView(PreventActionIfVisibiliteBrouillonMixin, FormView):
    template_name = "core/_structure_add_form.html"
    form_class = StructureAddForm

    def get_fiche_object(self):
        content_type_id = self.request.GET.get("content_type_id") or self.request.POST.get("content_type_id")
        fiche_id = self.request.GET.get("fiche_id") or self.request.POST.get("fiche_id")
        content_type = ContentType.objects.get(pk=content_type_id)
        ModelClass = content_type.model_class()
        return get_object_or_404(ModelClass, pk=fiche_id)

    def get_initial(self):
        initial = super().get_initial()
        initial["fiche_id"] = self.request.GET.get("fiche_id")
        initial["next"] = self.request.GET.get("next")
        initial["content_type_id"] = self.request.GET.get("content_type_id")
        return initial

    def form_valid(self, form):
        selection_form = StructureSelectionForm(
            fiche_id=form.cleaned_data.get("fiche_id"),
            content_type_id=form.cleaned_data.get("content_type_id"),
            structure_selected=form.cleaned_data.get("structure_niveau1"),
            initial={
                "next": form.cleaned_data.get("next"),
            },
        )
        return render(self.request, self.template_name, {"form": form, "selection_form": selection_form})


class StructureSelectionView(PreventActionIfVisibiliteBrouillonMixin, FormView):
    template_name = "core/_structure_add_form.html"
    form_class = StructureSelectionForm

    def get_fiche_object(self):
        content_type_id = self.request.POST.get("content_type_id")
        fiche_id = self.request.POST.get("fiche_id")
        content_type = ContentType.objects.get(pk=content_type_id)
        ModelClass = content_type.model_class()
        return get_object_or_404(ModelClass, pk=fiche_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = self.request.GET.get("next")
        return context

    def get_form_kwargs(self):
        kwargs = super(StructureSelectionView, self).get_form_kwargs()
        kwargs.update(
            {
                "fiche_id": self.request.POST.get("fiche_id", ""),
                "content_type_id": self.request.POST.get("content_type_id", ""),
                "structure_selected": self.request.POST.get("structure_selected", ""),
            }
        )
        return kwargs

    def form_invalid(self, form):
        add_form = StructureAddForm(
            initial={
                "fiche_id": form.data.get("fiche_id"),
                "content_type_id": form.data.get("content_type_id"),
                "next": form.data.get("next"),
                "structure_niveau1": form.data.get("structure_selected"),
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

    def form_valid(self, form):
        content_type = ContentType.objects.get(pk=form.cleaned_data["content_type_id"]).model_class()
        fiche = content_type.objects.get(pk=form.cleaned_data["fiche_id"])
        contacts = form.cleaned_data["contacts"]
        for contact in contacts:
            fiche.contacts.add(contact)

        message = ngettext(
            "La structure a été ajoutée avec succès.",
            "Les %(count)d structures ont été ajoutées avec succès.",
            len(contacts),
        ) % {"count": len(contacts)}
        messages.success(self.request, message, extra_tags="core contacts")

        return safe_redirect(self.request.POST.get("next") + "#tabpanel-contacts-panel")


class SoftDeleteView(View):
    def post(self, request):
        content_type_id = request.POST.get("content_type_id")
        content_id = request.POST.get("content_id")

        content_type = ContentType.objects.get(pk=content_type_id).model_class()
        obj = content_type.objects.get(pk=content_id)

        try:
            obj.soft_delete(request.user)
            messages.success(request, "Objet supprimé avec succès")
        except AttributeError:
            messages.error(request, "Ce type d'objet ne peut pas être supprimé")
        except PermissionDenied:
            messages.error(request, "Vous n'avez pas les droits pour supprimer cet objet")

        return safe_redirect(request.POST.get("next"))


class ACNotificationView(PreventActionIfVisibiliteBrouillonMixin, View):
    def get_fiche_object(self):
        content_type_id = self.request.POST.get("content_type_id")
        content_id = self.request.POST.get("content_id")
        content_type = ContentType.objects.get(pk=content_type_id).model_class()
        self.obj = content_type.objects.get(pk=content_id)
        return self.obj

    def post(self, request):
        try:
            self.obj.notify_ac(sender=self.request.user.agent.contact_set.get())
            messages.success(request, "L'administration centrale a été notifiée avec succès")
        except AttributeError:
            messages.error(request, "Ce type d'objet n'est pas compatible avec une notification à l'AC.")
        except ValidationError as e:
            messages.error(request, e.message)

        return safe_redirect(request.POST.get("next"))
