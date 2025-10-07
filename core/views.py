import logging
from functools import wraps

import requests
from celery.exceptions import OperationalError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import Media
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ngettext
from django.views import View
from django.views.generic import DetailView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormView, CreateView, UpdateView

from .forms import (
    DocumentUploadForm,
    MessageDocumentForm,
    DocumentEditForm,
    StructureAddForm,
    AgentAddForm,
)
from .mixins import (
    PreventActionIfVisibiliteBrouillonMixin,
    WithAddUserContactsMixin,
    WithPublishMixin,
    WithACNotificationMixin,
    MessageHandlingMixin,
    WithFormErrorsAsMessagesMixin,
)
from .models import Document, Message, Contact, user_is_referent_national
from .notifications import notify_contact_agent
from .redirect import safe_redirect

logger = logging.getLogger(__name__)


class MediaDefiningMixin(ContextMixin):
    def __new__(cls):
        """
        Wrapping get_context_data in a decorator here ensures get_media is called at the very last moment
        when all superclasses' get_context_data have been called.
        """

        def patch_get_context_data(get_context_data):
            @wraps(get_context_data)
            def wrapper(*args, **kwargs):
                context = get_context_data(*args, **kwargs)
                context.setdefault("media", obj.get_media(**context))
                return context

            return wrapper

        obj = super().__new__(cls)
        obj.get_context_data = patch_get_context_data(obj.get_context_data)
        return obj

    def get_media(self, **context_data) -> Media:
        return context_data["form"].media if "form" in context_data else Media()


class DocumentUploadView(
    PreventActionIfVisibiliteBrouillonMixin, WithAddUserContactsMixin, UserPassesTestMixin, FormView
):
    form_class = DocumentUploadForm

    def get_fiche_object(self):
        content_type = ContentType.objects.get(id=self.request.POST.get("content_type"))
        ModelClass = content_type.model_class()
        return get_object_or_404(ModelClass, pk=self.request.POST.get("object_id"))

    def test_func(self):
        return self.get_fiche_object().can_add_document(self.request.user)

    def post(self, request, *args, **kwargs):
        fiche = self.get_fiche_object()
        form = DocumentUploadForm(request.POST, request.FILES, obj=fiche)
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
        return self.get_fiche_object().can_delete_document(self.request.user)

    def post(self, request, *args, **kwargs):
        self.document.is_deleted = True
        self.document.deleted_by = self.request.user.agent
        self.document.save()
        messages.success(request, "Le document a été marqué comme supprimé.", extra_tags="core documents")
        return safe_redirect(request.POST.get("next") + "#tabpanel-documents-panel")


class DocumentUpdateView(
    PreventActionIfVisibiliteBrouillonMixin, UserPassesTestMixin, WithFormErrorsAsMessagesMixin, UpdateView
):
    model = Document
    form_class = DocumentEditForm
    http_method_names = ["post"]

    def test_func(self) -> bool | None:
        return self.get_fiche_object().can_update_document(self.request.user)

    def get_fiche_object(self):
        self.document = get_object_or_404(Document, pk=self.kwargs.get("pk"))
        if isinstance(self.document.content_object, Message):
            return self.document.content_object.content_object
        return self.document.content_object

    def get_success_url(self):
        return self.get_fiche_object().get_absolute_url() + "#tabpanel-documents-panel"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Le document a bien été mis à jour.", extra_tags="core documents")
        return response

    def form_invalid(self, form):
        super().form_invalid(form)
        return safe_redirect(self.get_success_url())


class ContactDeleteView(PreventActionIfVisibiliteBrouillonMixin, UserPassesTestMixin, View):
    def get_fiche_object(self):
        content_type = ContentType.objects.get(id=self.request.POST.get("content_type_pk"))
        ModelClass = content_type.model_class()
        self.fiche = get_object_or_404(ModelClass, pk=self.request.POST.get("fiche_pk"))
        return self.fiche

    def test_func(self):
        return self.get_fiche_object().can_delete_contact(self.request.user)

    def post(self, request, *args, **kwargs):
        contact = Contact.objects.get(pk=self.request.POST.get("pk"))
        self.fiche.contacts.remove(contact)
        messages.success(request, "Le contact a bien été supprimé de la fiche.", extra_tags="core contacts")
        return safe_redirect(request.POST.get("next") + "#tabpanel-contacts-panel")


class MessageCreateView(
    PreventActionIfVisibiliteBrouillonMixin,
    UserPassesTestMixin,
    MessageHandlingMixin,
    CreateView,
):
    model = Message
    http_method_names = ["post"]

    def get_form_class(self):
        return self.obj.get_message_form()

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
        context["add_document_form"] = MessageDocumentForm(object=self.obj)
        return context

    def get_success_url(self):
        return self.obj.get_absolute_url() + "#tabpanel-messages-panel"

    def form_valid(self, form):
        return self.handle_message_form(form)

    def form_invalid(self, form):
        for _, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return HttpResponseRedirect(self.obj.get_absolute_url())


class MessageUpdateView(
    PreventActionIfVisibiliteBrouillonMixin,
    UserPassesTestMixin,
    MessageHandlingMixin,
    UpdateView,
):
    model = Message
    http_method_names = ["post"]

    def get_form_class(self):
        return self.content_object.get_message_form()

    def dispatch(self, request, *args, **kwargs):
        self.content_object = self.get_object().content_object
        self.obj = self.content_object
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.get_object().can_be_updated(self.request.user)

    def get_fiche_object(self):
        return self.content_object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["sender"] = self.request.user.agent.contact_set.get()
        kwargs["obj"] = self.content_object
        kwargs["next"] = self.content_object.get_absolute_url()
        return kwargs

    def get_success_url(self):
        return self.content_object.get_absolute_url() + "#tabpanel-messages-panel"

    def form_valid(self, form):
        return self.handle_message_form(form)


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


class PublishView(WithPublishMixin, View):
    def post(self, request):
        content_type_id = request.POST.get("content_type_id")
        content_id = request.POST.get("content_id")

        content_type = ContentType.objects.get(pk=content_type_id).model_class()
        obj = content_type.objects.get(pk=content_id)

        self.publish(obj, request)
        return safe_redirect(request.POST.get("next"))


class ACNotificationView(PreventActionIfVisibiliteBrouillonMixin, UserPassesTestMixin, WithACNotificationMixin, View):
    def test_func(self):
        return self.obj.can_user_access(self.request.user)

    def get_fiche_object(self):
        content_type_id = self.request.POST.get("content_type_id")
        content_id = self.request.POST.get("content_id")
        content_type = ContentType.objects.get(pk=content_type_id).model_class()
        self.obj = content_type.objects.get(pk=content_id)
        return self.obj

    def post(self, request):
        self.notify_ac(self.obj, request)
        return safe_redirect(request.POST.get("next"))


class PublishAndACNotificationView(WithPublishMixin, WithACNotificationMixin, View):
    def post(self, request):
        content_type_id = request.POST.get("content_type_id")
        content_id = request.POST.get("content_id")
        content_type = ContentType.objects.get(pk=content_type_id).model_class()
        obj = content_type.objects.get(pk=content_id)
        if not self.publish(obj, request):
            return safe_redirect(request.POST.get("next"))
        self.notify_ac(obj, request)
        return safe_redirect(request.POST.get("next"))


class StructureAddView(PreventActionIfVisibiliteBrouillonMixin, UserPassesTestMixin, View):
    http_method_names = ["post"]

    def get_fiche_object(self):
        content_type_id = self.request.POST.get("content_type_id")
        content_id = self.request.POST.get("content_id")
        model_class = ContentType.objects.get(pk=content_type_id).model_class()
        self.obj = model_class.objects.get(pk=content_id)
        return self.obj

    def test_func(self) -> bool | None:
        return self.get_fiche_object().can_add_structure(self.request.user)

    def post(self, request, *args, **kwargs):
        form = StructureAddForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Erreur lors de l'ajout de la structure.")
            return safe_redirect(self.obj.get_absolute_url() + "#tabpanel-contacts-panel")

        self.obj = self.get_fiche_object()
        contacts_structures = form.cleaned_data["contacts_structures"]
        with transaction.atomic():
            for contact_structure in contacts_structures:
                self.obj.contacts.add(contact_structure)
            if hasattr(self.obj, "update_allowed_structures_and_visibility"):
                self.obj.update_allowed_structures_and_visibility(contacts_structures)

        message = ngettext(
            "La structure a été ajoutée avec succès.",
            "Les %(count)d structures ont été ajoutées avec succès.",
            len(contacts_structures),
        ) % {"count": len(contacts_structures)}
        messages.success(request, message, extra_tags="core contacts")
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
        return self.get_fiche_object().can_add_agent(self.request.user)

    def post(self, request, *args, **kwargs):
        form = AgentAddForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Erreur lors de l'ajout de l'agent.")
            return safe_redirect(self.obj.get_absolute_url() + "#tabpanel-contacts-panel")

        self.obj = self.get_fiche_object()
        contacts_agents = form.cleaned_data["contacts_agents"]
        allowed_contacts_structures_to_add = []
        with transaction.atomic():
            for contact_agent in contacts_agents:
                self.obj.contacts.add(contact_agent)
                if not user_is_referent_national(contact_agent.agent.user):
                    contact_structure = contact_agent.get_structure_contact()
                    self.obj.contacts.add(contact_structure)
                    allowed_contacts_structures_to_add.append(contact_structure)
            if hasattr(self.obj, "update_allowed_structures_and_visibility"):
                self.obj.update_allowed_structures_and_visibility(allowed_contacts_structures_to_add)
            notify_contact_agent(contact_agent, self.obj)

        message = ngettext(
            "L'agent a été ajouté avec succès.",
            "Les %(count)d agents ont été ajoutés avec succès.",
            len(contacts_agents),
        ) % {"count": len(contacts_agents)}
        messages.success(request, message, extra_tags="core contacts")
        return safe_redirect(self.obj.get_absolute_url() + "#tabpanel-contacts-panel")


class CloturerView(View):
    def post(self, request, pk):
        data = self.request.POST
        content_type = ContentType.objects.get(pk=data["content_type_id"])
        object = content_type.model_class().objects.get(pk=pk)
        redirect_url = object.get_absolute_url()

        can_cloturer, error_message = object.can_be_cloture(request.user)
        if not can_cloturer:
            messages.error(request, error_message)
            return redirect(redirect_url)

        if object.is_the_only_remaining_structure(self.request.user, object.get_contacts_structures_not_in_fin_suivi()):
            object.add_fin_suivi(self.request.user)

        object.cloturer()
        messages.success(request, object.get_cloture_confirm_message())
        return redirect(redirect_url)


class EvenementOuvrirView(View):
    def post(self, request, pk):
        data = self.request.POST
        content_type = ContentType.objects.get(pk=data["content_type_id"])
        obj = content_type.model_class().objects.get(pk=pk)
        redirect_url = obj.get_absolute_url()
        if not obj.can_ouvrir(request.user):
            messages.error(request, "Vous ne pouvez pas ouvrir l'évènement.")
            return redirect(redirect_url)
        with transaction.atomic():
            user_contact = self.request.user.agent.structure.contact_set.get()
            if fin_suivi := obj.fin_suivi.filter(contact=user_contact):
                fin_suivi.delete()
            obj.publish()
            messages.success(request, f"L'événement {obj.numero} a bien été ouvert de nouveau.")
            return redirect(redirect_url)


def sirene_api(request, siret: str):
    if not settings.SIRENE_API_KEY or not settings.SIRENE_API_BASE:
        return HttpResponse(status=401)

    siret = siret.replace(" ", "")[:9]

    if not siret.isnumeric() or len(siret) < 5:
        return HttpResponseServerError()

    try:
        response = requests.get(
            f"{settings.SIRENE_API_BASE.removesuffix('/')}/siret",
            params={"q": f"siren:{siret}* AND -periode(etatAdministratifEtablissement:F)", "nombre": "100"},
            headers={"X-INSEE-Api-Key-Integration": settings.SIRENE_API_KEY},
            timeout=4,
        )
        if response.status_code != 200:
            return HttpResponseServerError()

        return JsonResponse(response.json())
    except Exception as e:
        logger.exception(e)
        return HttpResponseServerError()
