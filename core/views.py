import contextlib
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect
from django.http.response import HttpResponse, HttpResponseServerError, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ngettext
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, FormView, UpdateView
import requests
from reversion.models import Version

from core.diffs import CompareMixin, Diff, get_diff_from_comment_version

from .forms import (
    AgentAddForm,
    BasicMessageForm,
    DemandeInterventionForm,
    DocumentEditForm,
    DocumentUploadForm,
    NoteForm,
    PointDeSituationForm,
    StructureAddForm,
)
from .mixins import (
    MessageHandlingMixin,
    PreventActionIfVisibiliteBrouillonMixin,
    WithACNotificationMixin,
    WithAddUserContactsMixin,
    WithEtatMixin,
    WithFormErrorsAsMessagesMixin,
    WithPublishMixin,
)
from .models import Contact, Document, FinSuiviContact, Message, user_is_referent_national
from .notifications import notify_contact_agent_added_or_removed
from .redirect import safe_redirect

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class DocumentUploadView(
    PreventActionIfVisibiliteBrouillonMixin, WithAddUserContactsMixin, UserPassesTestMixin, FormView
):
    form_class = DocumentUploadForm
    template_name = "core/form/document_upload.html#form_content"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.document = None
        with contextlib.suppress(Document.DoesNotExist):
            self.document = self.fiche_objet.documents.get(pk=self.request.POST.get("id"))

    def get_fiche_object(self):
        content_type = ContentType.objects.get(id=self.request.POST.get("content_type"))
        ModelClass = content_type.model_class()
        return get_object_or_404(ModelClass, pk=self.request.POST.get("object_id"))

    def test_func(self):
        return self.get_fiche_object().can_add_document(self.request.user)

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "user": self.request.user,
            "allowed_document_types": self.fiche_objet.get_allowed_document_types(),
            "related_to": self.fiche_objet,
            "data": self.request.POST,
            "files": self.request.FILES,
            "instance": self.document,
        }

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=400)

    def form_valid(self, form):
        form.save()
        self.add_user_contacts(self.fiche_objet)
        return super().render_to_response(self.get_context_data(form=form))


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
        notify_contact_agent_added_or_removed(contact, self.fiche, added=False, user=self.request.user)
        messages.success(request, "Le contact a bien été supprimé de la fiche.", extra_tags="core contacts")
        return safe_redirect(request.POST.get("next") + "#tabpanel-contacts-panel")


class MessageCreateView(
    PreventActionIfVisibiliteBrouillonMixin,
    UserPassesTestMixin,
    MessageHandlingMixin,
    CreateView,
):
    model = Message

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.reply_message = None

    def get_fiche_object(self):
        self.fiche_object_class = ContentType.objects.get(pk=self.kwargs.get("obj_type_pk")).model_class()
        return get_object_or_404(self.fiche_object_class, pk=self.kwargs.get("obj_pk"))

    def get_form_class(self):
        mapping = {
            "message": BasicMessageForm,
            "note": NoteForm,
            "point_situation": PointDeSituationForm,
            "demande_intervention": DemandeInterventionForm,
            "cr_demande_intervention": self.fiche_objet.get_crdi_form(),
        }
        self.reply_id = self.request.GET.get("reply_id")
        if self.reply_id:
            return BasicMessageForm
        message_form = mapping.get(self.request.GET.get("type"))

        is_ac = self.request.user.agent.structure.is_ac
        if message_form == DemandeInterventionForm and not is_ac:
            raise PermissionDenied
        if message_form == self.fiche_objet.get_crdi_form() and is_ac:
            raise PermissionDenied
        return message_form

    def test_func(self) -> bool | None:
        return self.fiche_objet.can_user_access(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "obj": self.fiche_objet,
                "sender": self.request.user.agent.contact_set.get(),
            }
        )
        if self.request.GET.get("contact"):
            kwargs.update({"initial": {"recipients": [self.request.GET.get("contact")]}})
        if self.reply_id:
            reply_message = Message.objects.get(id=self.reply_id)
            self.reply_message = reply_message
            if reply_message.can_reply_to(self.request.user):
                title = reply_message.title
                if not reply_message.title.startswith(settings.REPLY_PREFIX):
                    title = f"{settings.REPLY_PREFIX} {reply_message.title}"
                kwargs.update(
                    {
                        "initial": {
                            "title": title,
                            "recipients": reply_message.sender_structure.contact_set.get(),
                            "content": reply_message.get_reply_intro_text(),
                        }
                    }
                )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["go_back_url"] = self.fiche_objet.get_absolute_url()
        context["message_status"] = Message.Status
        if self.reply_message:
            context["page_title"] = self.reply_message.reply_page_title
        return context

    def get_success_url(self):
        return self.fiche_objet.get_absolute_url() + "#tabpanel-messages-panel"

    def form_valid(self, form):
        return self.handle_message_form(form)

    def form_invalid(self, form):
        for _, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return HttpResponseRedirect(self.fiche_objet.get_absolute_url())


class MessageUpdateView(
    PreventActionIfVisibiliteBrouillonMixin,
    UserPassesTestMixin,
    MessageHandlingMixin,
    UpdateView,
):
    model = Message
    context_object_name = "message"

    def get_fiche_object(self):
        return self.get_object().content_object

    def get_form_class(self):
        mapping = {
            Message.MESSAGE: BasicMessageForm,
            Message.NOTE: NoteForm,
            Message.POINT_DE_SITUATION: PointDeSituationForm,
            Message.DEMANDE_INTERVENTION: DemandeInterventionForm,
            Message.COMPTE_RENDU: self.fiche_objet.get_crdi_form(),
        }
        return mapping.get(self.object.message_type)

    def test_func(self):
        return self.get_object().can_be_updated(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["sender"] = self.request.user.agent.contact_set.get()
        kwargs["obj"] = self.fiche_objet
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["go_back_url"] = self.fiche_objet.get_absolute_url()
        context["message_status"] = Message.Status
        return context

    def get_success_url(self):
        return self.fiche_objet.get_absolute_url() + "#tabpanel-messages-panel"

    def form_valid(self, form):
        return self.handle_message_form(form)


class MessageDetailsView(PreventActionIfVisibiliteBrouillonMixin, UserPassesTestMixin, DetailView):
    model = Message

    def get_queryset(self):
        return Message.objects.select_related("sender__agent__structure", "sender_structure").prefetch_related(
            "recipients__agent",
            "recipients__structure",
            "recipients__agent__structure",
            "recipients_copy__agent",
            "recipients_copy__structure",
            "recipients_copy__agent__structure",
            "documents",
        )

    def dispatch(self, request, *args, **kwargs):
        self.message = get_object_or_404(Message, pk=self.kwargs.get("pk"))
        self.fiche = self.message.content_object
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.fiche.can_user_access(self.request.user)

    def get_fiche_object(self):
        return self.fiche

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_download_document"] = self.fiche.can_download_document(self.request.user)
        context["can_reply_to"] = self.message.can_reply_to(self.request.user)
        return context


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
        self.obj = self.get_fiche_object()

        form = StructureAddForm(request.POST, obj=self.obj)
        if not form.is_valid():
            messages.error(request, "Erreur lors de l'ajout de la structure.")
            return safe_redirect(self.obj.get_absolute_url() + "#tabpanel-contacts-panel")

        contacts_structures = form.cleaned_data["contacts_structures"]
        with transaction.atomic():
            for contact_structure in contacts_structures:
                self.obj.contacts.add(contact_structure)
                notify_contact_agent_added_or_removed(contact_structure, self.obj, added=True, user=self.request.user)
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
        self.obj = self.get_fiche_object()
        form = AgentAddForm(request.POST, obj=self.obj)
        if not form.is_valid():
            messages.error(request, "Erreur lors de l'ajout de l'agent.")
            return safe_redirect(self.obj.get_absolute_url() + "#tabpanel-contacts-panel")

        contacts_agents = form.cleaned_data["contacts_agents"]
        allowed_contacts_structures_to_add = []
        with transaction.atomic():
            for contact_agent in contacts_agents:
                self.obj.contacts.add(contact_agent)
                notify_contact_agent_added_or_removed(contact_agent, self.obj, added=True, user=self.request.user)
                if not user_is_referent_national(contact_agent.agent.user):
                    contact_structure = contact_agent.get_structure_contact()
                    self.obj.contacts.add(contact_structure)
                    allowed_contacts_structures_to_add.append(contact_structure)
            if hasattr(self.obj, "update_allowed_structures_and_visibility"):
                self.obj.update_allowed_structures_and_visibility(allowed_contacts_structures_to_add)

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
            object.add_fin_suivi(structure=self.request.user.agent.structure, made_by=self.request.user)

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


class FinDeSuiviHandlingView(View):
    http_method_names = ["post"]

    def post(self, request):
        data = self.request.POST
        content_type = ContentType.objects.get(pk=data.get("content_type"))
        object = content_type.model_class().objects.get(pk=data.get("pk"))

        if data["mode"] == "add":
            if not FinSuiviContact.can_add_fin_de_suivi(object, self.request.user):
                messages.error(request, "Vous ne pouvez pas mettre fin au suivi de l'évènement.")
                return redirect(object.get_absolute_url())

            object.add_fin_suivi(structure=self.request.user.agent.structure, made_by=self.request.user)
            messages.success(request, "Fin de suivi réalisée avec succès.")
            return redirect(object.get_absolute_url())

        if data["mode"] == "remove":
            if not FinSuiviContact.can_remove_fin_de_suivi(object, self.request.user):
                messages.error(request, "Vous ne pouvez pas reprendre le suivi de l'évènement.")
                return redirect(object.get_absolute_url())

            object.remove_fin_suivi(self.request.user)
            messages.success(request, "La reprise de suivi a été prise en compte.")
            return redirect(object.get_absolute_url())

        raise NotImplementedError


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


class RevisionsListView(UserPassesTestMixin, CompareMixin, ListView):
    compare_exclude = [
        "date_derniere_mise_a_jour",
    ]

    def dispatch(self, request, *args, **kwargs):
        content_type = ContentType.objects.get(id=kwargs["content_type"])
        self.object = content_type.model_class().objects.get(pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.object.can_user_access(self.request.user)

    def get_queryset(self):
        return (
            Version.objects.get_for_object(self.object)
            .select_related("revision", "revision__user__agent__structure")
            .order_by("-revision__date_created")
            .exclude(serialized_data={})
        )

    def get_initial_patch(self, versions):
        etat_value = json.loads(list(versions)[-1].serialized_data)[0]["fields"]["etat"]
        readable_etat = WithEtatMixin.Etat(etat_value).label
        return Diff(field="Statut", old="Vide", new=readable_etat, revision=list(versions)[-1].revision)

    def get_comment_versions(self):
        return (
            Version.objects.get_for_object(self.object)
            .select_related("revision", "revision__user__agent__structure")
            .order_by("-revision__date_created")
            .filter(serialized_data={})
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object

        versions = context["object_list"]
        if not versions:
            return context

        context["patches"] = [self.get_initial_patch(versions)]
        for i in range(1, len(versions)):
            diffs, _ = self.compare(self.object, versions[i], versions[i - 1])
            context["patches"].extend(diffs)

        for version in self.get_comment_versions():
            comment_diff = get_diff_from_comment_version(version)
            if comment_diff:
                context["patches"].append(comment_diff)

        context["patches"] = sorted(context["patches"], key=lambda x: x.date_created, reverse=True)
        return context
