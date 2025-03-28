from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ngettext
from django.views import View
from django.views.generic import DetailView
from celery.exceptions import OperationalError
from django.views.generic.edit import FormView, CreateView, UpdateView
from sv.view_mixins import WithAddUserContactsMixin
from .forms import (
    DocumentUploadForm,
    MessageForm,
    MessageDocumentForm,
    DocumentEditForm,
    StructureAddForm,
    AgentAddForm,
)
from .mixins import PreventActionIfVisibiliteBrouillonMixin
from .models import Document, Message, Contact, FinSuiviContact, Visibilite
from .notifications import notify_message
from .redirect import safe_redirect
import logging

logger = logging.getLogger(__name__)


class DocumentUploadView(
    PreventActionIfVisibiliteBrouillonMixin, WithAddUserContactsMixin, UserPassesTestMixin, FormView
):
    form_class = DocumentUploadForm

    def get_fiche_object(self):
        content_type = ContentType.objects.get(id=self.request.POST.get("content_type"))
        ModelClass = content_type.model_class()
        return get_object_or_404(ModelClass, pk=self.request.POST.get("object_id"))

    def test_func(self):
        return self.get_fiche_object().can_user_access(self.request.user)

    def post(self, request, *args, **kwargs):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            agent = request.user.agent
            document.created_by = agent
            document.created_by_structure = agent.structure
            try:
                document.save()
            except OperationalError:
                messages.error(
                    request, "Une erreur s'est produite lors de l'ajout du document.", extra_tags="core documents"
                )
                logger.error("Could not connect to Redis")
                return safe_redirect(self.request.POST.get("next") + "#tabpanel-documents-panel")

            fiche = self.get_fiche_object()
            self.add_user_contacts(fiche)

            messages.success(
                request,
                "Le document a été ajouté avec succès, il sera disponible après l'analyse antivirus.",
                extra_tags="core documents",
            )
            return safe_redirect(self.request.POST.get("next") + "#tabpanel-documents-panel")

        messages.error(request, "Une erreur s'est produite lors de l'ajout du document", extra_tags="core documents")
        for _, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error, extra_tags="core documents")
        return safe_redirect(self.request.POST.get("next") + "#tabpanel-documents-panel")


class DocumentDeleteView(PreventActionIfVisibiliteBrouillonMixin, UserPassesTestMixin, View):
    def get_fiche_object(self):
        self.document = get_object_or_404(Document, pk=self.kwargs.get("pk"))

        if isinstance(self.document.content_object, Message):
            return self.document.content_object.content_object
        return self.document.content_object

    def test_func(self):
        return self.get_fiche_object().can_user_access(self.request.user)

    def post(self, request, *args, **kwargs):
        self.document.is_deleted = True
        self.document.deleted_by = self.request.user.agent
        self.document.save()
        messages.success(request, "Le document a été marqué comme supprimé.", extra_tags="core documents")
        return safe_redirect(request.POST.get("next") + "#tabpanel-documents-panel")


class DocumentUpdateView(PreventActionIfVisibiliteBrouillonMixin, UserPassesTestMixin, UpdateView):
    model = Document
    form_class = DocumentEditForm
    http_method_names = ["post"]

    def test_func(self) -> bool | None:
        return self.get_fiche_object().can_user_access(self.request.user)

    def get_fiche_object(self):
        self.document = get_object_or_404(Document, pk=self.kwargs.get("pk"))
        return self.document.content_object

    def get_success_url(self):
        return self.request.POST.get("next") + "#tabpanel-documents-panel"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Le document a bien été mis à jour.", extra_tags="core documents")
        return response


class ContactDeleteView(PreventActionIfVisibiliteBrouillonMixin, UserPassesTestMixin, View):
    def get_fiche_object(self):
        content_type = ContentType.objects.get(id=self.request.POST.get("content_type_pk"))
        ModelClass = content_type.model_class()
        self.fiche = get_object_or_404(ModelClass, pk=self.request.POST.get("fiche_pk"))
        return self.fiche

    def test_func(self):
        return self.get_fiche_object().can_user_access(self.request.user)

    def post(self, request, *args, **kwargs):
        contact = Contact.objects.get(pk=self.request.POST.get("pk"))
        self.fiche.contacts.remove(contact)
        messages.success(request, "Le contact a bien été supprimé de la fiche.", extra_tags="core contacts")
        return safe_redirect(request.POST.get("next") + "#tabpanel-contacts-panel")


class MessageCreateView(
    PreventActionIfVisibiliteBrouillonMixin, WithAddUserContactsMixin, UserPassesTestMixin, CreateView
):
    model = Message
    form_class = MessageForm
    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        self.obj_class = ContentType.objects.get(pk=self.kwargs.get("obj_type_pk")).model_class()
        self.obj = get_object_or_404(self.obj_class, pk=self.kwargs.get("obj_pk"))
        return super().dispatch(request, *args, **kwargs)

    def test_func(self) -> bool | None:
        return self.get_fiche_object().can_user_access(self.request.user)

    def get_fiche_object(self):
        return self.obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "obj": self.obj,
                "next": self.obj.get_absolute_url(),
                "sender": self.request.user.agent.contact_set.get(),
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["go_back_url"] = self.obj.get_absolute_url()
        context["add_document_form"] = MessageDocumentForm()
        return context

    def get_success_url(self):
        return self.obj.get_absolute_url() + "#tabpanel-messages-panel"

    def _add_contacts_to_object(self, message):
        for contact in message.recipients.all().union(message.recipients_copy.all()):
            self.obj.contacts.add(contact)

            if structure := contact.get_structure_contact():
                self.obj.contacts.add(structure)

    def _is_internal_communication(self, structures):
        """
        Returns True if all contacts involved are part of the same structure
        """
        return len(structures) <= 1

    def _handle_visibilite_if_needed(self, message):
        if not hasattr(self.obj, "visibilite"):
            return

        structures = [c.structure for c in self.obj.contacts.structures_only()]

        if self._is_internal_communication(structures):
            return
        if self.obj.visibilite == Visibilite.LOCALE:
            with transaction.atomic():
                self.obj.allowed_structures.set(structures)
                self.obj.visibilite = Visibilite.LIMITEE
                self.obj.save()
        if self.obj.visibilite == Visibilite.LIMITEE:
            self.obj.allowed_structures.set(structures)

    def _create_documents(self, form):
        message = form.instance
        content_type = ContentType.objects.get_for_model(message)
        document_numbers = [
            s.replace("document_type_", "") for s in form.cleaned_data.keys() if s.startswith("document_type_")
        ]
        for i in document_numbers:
            try:
                Document.objects.create(
                    file=form.cleaned_data[f"document_{i}"],
                    nom=form.cleaned_data[f"document_{i}"]._name,
                    document_type=form.cleaned_data[f"document_type_{i}"],
                    content_type=content_type,
                    object_id=message.pk,
                    created_by=self.request.user.agent,
                    created_by_structure=self.request.user.agent.structure,
                )
            except OperationalError:
                logger.error("Could not connect to Redis")
                messages.error("Une erreur s'est produite lors de l'ajout du document.", extra_tags="core messages")

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
        self.add_user_contacts(self.obj)
        self._handle_visibilite_if_needed(form.instance)
        self._create_documents(form)
        try:
            notify_message(form.instance)
        except OperationalError:
            messages.error(
                self.request, "Une erreur s'est produite lors de l'envoi du message.", extra_tags="core messages"
            )
            logger.error("Could not connect to Redis")

        else:
            messages.success(self.request, "Le message a bien été ajouté.", extra_tags="core messages")
        return response

    def form_invalid(self, form):
        for _, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return HttpResponseRedirect(self.obj.get_absolute_url())


class MessageDetailsView(PreventActionIfVisibiliteBrouillonMixin, DetailView):
    model = Message

    def get_fiche_object(self):
        message = get_object_or_404(Message, pk=self.kwargs.get("pk"))
        fiche = message.content_object
        return fiche


class SoftDeleteView(View):
    def post(self, request):
        content_type_id = request.POST.get("content_type_id")
        content_id = request.POST.get("content_id")

        content_type = ContentType.objects.get(pk=content_type_id).model_class()
        obj = content_type.objects.get(pk=content_id)

        try:
            obj.soft_delete(request.user)
            messages.success(request, obj.get_soft_delete_success_message())
        except AttributeError:
            messages.error(request, obj.get_soft_delete_attribute_error_message())
        except PermissionDenied:
            messages.error(request, obj.get_soft_delete_permission_error_message())

        return safe_redirect(request.POST.get("next"))


class PublishView(View):
    def post(self, request):
        content_type_id = request.POST.get("content_type_id")
        content_id = request.POST.get("content_id")

        content_type = ContentType.objects.get(pk=content_type_id).model_class()
        obj = content_type.objects.get(pk=content_id)

        if obj.can_publish(request.user):
            obj.publish()
            messages.success(request, obj.get_publish_success_message())
        else:
            messages.error(request, obj.get_publish_error_message())
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
            self.obj.notify_ac(user=self.request.user)
            messages.success(request, "L'administration centrale a été notifiée avec succès")
        except AttributeError:
            messages.error(request, "Ce type d'objet n'est pas compatible avec une notification à l'AC.")
        except ValidationError as e:
            messages.error(request, e.message)

        return safe_redirect(request.POST.get("next"))


class WithFormErrorsAsMessagesMixin(FormView):
    def form_invalid(self, form):
        for _, errors in form.errors.as_data().items():
            for error in errors:
                if error.code == "blocking_error":
                    messages.error(self.request, error.message, extra_tags="blocking")
                else:
                    messages.error(self.request, error.message)
        return super().form_invalid(form)


class StructureAddView(PreventActionIfVisibiliteBrouillonMixin, UserPassesTestMixin, View):
    http_method_names = ["post"]

    def get_fiche_object(self):
        content_type_id = self.request.POST.get("content_type_id")
        content_id = self.request.POST.get("content_id")
        model_class = ContentType.objects.get(pk=content_type_id).model_class()
        self.obj = model_class.objects.get(pk=content_id)
        return self.obj

    def test_func(self) -> bool | None:
        return self.get_fiche_object().can_user_access(self.request.user)

    def post(self, request, *args, **kwargs):
        form = StructureAddForm(request.POST)
        if form.is_valid():
            self.obj = self.get_fiche_object()
            contacts_structures = form.cleaned_data["contacts_structures"]
            for structure in contacts_structures:
                self.obj.contacts.add(structure)

            message = ngettext(
                "La structure a été ajoutée avec succès.",
                "Les %(count)d structures ont été ajoutées avec succès.",
                len(contacts_structures),
            ) % {"count": len(contacts_structures)}
            messages.success(request, message, extra_tags="core contacts")
            return safe_redirect(self.obj.get_absolute_url() + "#tabpanel-contacts-panel")

        messages.error(request, "Erreur lors de l'ajout de la structure.")
        return safe_redirect(self.obj.get_absolute_url() + "#tabpanel-contacts-panel")


class AgentAddView(PreventActionIfVisibiliteBrouillonMixin, UserPassesTestMixin, View):
    http_method_names = ["post"]

    def get_fiche_object(self):
        content_type_id = self.request.POST.get("content_type_id")
        content_id = self.request.POST.get("content_id")
        model_class = ContentType.objects.get(pk=content_type_id).model_class()
        self.obj = model_class.objects.get(pk=content_id)
        return self.obj

    def test_func(self) -> bool | None:
        return self.get_fiche_object().can_user_access(self.request.user)

    def post(self, request, *args, **kwargs):
        form = AgentAddForm(request.POST)
        if form.is_valid():
            self.obj = self.get_fiche_object()
            contacts_agents = form.cleaned_data["contacts_agents"]
            for contact_agent in contacts_agents:
                self.obj.contacts.add(contact_agent)
                if contact_structure := contact_agent.get_structure_contact():
                    self.obj.contacts.add(contact_structure)

            message = ngettext(
                "L'agent a été ajouté avec succès.",
                "Les %(count)d agents ont été ajoutés avec succès.",
                len(contacts_agents),
            ) % {"count": len(contacts_agents)}
            messages.success(request, message, extra_tags="core contacts")
            return safe_redirect(self.obj.get_absolute_url() + "#tabpanel-contacts-panel")

        messages.error(request, "Erreur lors de l'ajout de l'agent.")
        return safe_redirect(self.obj.get_absolute_url() + "#tabpanel-contacts-panel")
