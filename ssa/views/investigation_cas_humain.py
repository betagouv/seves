import datetime
import io
import os
from functools import cached_property

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.forms import Media
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, UpdateView
from django.views.generic.detail import BaseDetailView
from docxtpl import DocxTemplate
from reversion.models import Version

from core.mixins import (
    WithAddUserContactsMixin,
    WithBlocCommunPermission,
    WithClotureContextMixin,
    WithContactFormsInContextMixin,
    WithContactListInContextMixin,
    WithDocumentExportContextMixin,
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithFinDeSuiviMixin,
    WithFormErrorsAsMessagesMixin,
    WithFreeLinksListInContextMixin,
    WithMessageMixin,
    WithFormsetInvalidMixin,
    MediaDefiningMixin,
)

from ..forms import InvestigationCasHumainForm
from ..formsets import InvestigationCasHumainsEtablissementFormSet
from ..models import EvenementInvestigationCasHumain
from ..notifications import notify_souches_clusters
from .mixins import EvenementProduitValuesMixin


class InvestigationCasHumainCreateView(
    WithFormErrorsAsMessagesMixin,
    WithAddUserContactsMixin,
    EvenementProduitValuesMixin,
    MediaDefiningMixin,
    WithFormsetInvalidMixin,
    CreateView,
):
    template_name = "ssa/evenement_investigation_cas_humain.html"
    form_class = InvestigationCasHumainForm
    success_message = "L’évènement Investigation de cas humain a été créé avec succès."

    @property
    def etablissement_formset(self):
        if not hasattr(self, "_etablissement_formset"):
            self._etablissement_formset = InvestigationCasHumainsEtablissementFormSet(**super().get_form_kwargs())
        return self._etablissement_formset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, etablissement_formset=self.etablissement_formset)

    def get_media(self, **context_data) -> Media:
        return super().get_media(**context_data) + context_data["etablissement_formset"].media

    def form_valid(self, form):
        self.object = form.save()
        self.etablissement_formset.instance = self.object
        self.etablissement_formset.save()
        self.add_user_contacts(self.object)

        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.object.get_absolute_url())

    def post(self, request, *args, **kwargs):
        if not self.etablissement_formset.is_valid():
            self.object = None
            return self.formset_invalid(
                self.etablissement_formset,
                "Erreurs dans le(s) formulaire(s) Établissements",
                "Erreur dans le formulaire établissement",
            )

        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)
        return self.form_valid(form)


class InvestigationCasHumainUpdateView(InvestigationCasHumainCreateView, UpdateView):
    success_message = "L'évènement Investigation cas humain a bien été modifié."

    @property
    def object(self):
        if not hasattr(self, "_object"):
            self._object = self.get_object()
        return self._object

    @object.setter
    def object(self, value):
        self._object = value

    def get_queryset(self):
        return EvenementInvestigationCasHumain.objects.with_departement_prefetched()

    def _trigger_notifications(self):
        dirty_fields = self.object.get_dirty_fields()
        if ("reference_souches" in dirty_fields) or ("reference_clusters" in dirty_fields):
            notify_souches_clusters(self.object, self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["latest_version"] = Version.objects.get_for_object(self.get_object()).first().pk
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self._trigger_notifications()
        self.object.save()
        self.etablissement_formset.instance = self.object
        self.etablissement_formset.save()
        self.add_user_contacts(self.object)

        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.object.get_absolute_url())


class InvestigationCasHumainDetailView(
    UserPassesTestMixin,
    WithFreeLinksListInContextMixin,
    WithClotureContextMixin,
    WithBlocCommunPermission,
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithMessageMixin,
    WithContactFormsInContextMixin,
    WithContactListInContextMixin,
    WithFinDeSuiviMixin,
    DetailView,
):
    model = EvenementInvestigationCasHumain
    template_name = "ssa/investigation_cas_humain_detail.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_queryset(self):
        return (
            EvenementInvestigationCasHumain.objects.all()
            .select_related("createur")
            .prefetch_related("etablissements__departement")
            .prefetch_related("etablissements__departement__region")
        )

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        if queryset is None:
            queryset = self.get_queryset()
        try:
            self.object = queryset.get(pk=self.kwargs["pk"])
            return self.object
        except (ValueError, EvenementInvestigationCasHumain.DoesNotExist):
            raise Http404("Fiche produit non trouvée")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.request.user.agent.structure.contact_set.get()
        context["etat"] = self.get_object().get_etat_data_for_contact(contact)
        context["can_be_deleted"] = self.get_object().can_be_deleted(self.request.user)
        context["can_publish"] = self.get_object().can_publish(self.request.user)
        context["can_be_modified"] = self.get_object().can_be_modified(self.request.user)
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        return context


class InvestigationCasHumainDocumentExportView(WithDocumentExportContextMixin, UserPassesTestMixin, BaseDetailView):
    http_method_names = ["post"]
    model = EvenementInvestigationCasHumain

    @cached_property
    def object(self):
        return self.get_object()

    def test_func(self):
        return self.object.can_user_access(self.request.user)

    def post(self, request, *args, **kwargs):
        doc = DocxTemplate("ssa/doc_templates/investigation_cas_humain.docx")
        sub_doc_file = self.create_document_bloc_commun()
        sub_doc = doc.new_subdoc(sub_doc_file)

        context = self.get_context_data(
            object=self.object,
            free_links=self.get_free_links_numbers(),
            bloc_commun=sub_doc,
            now=datetime.datetime.now(),
        )
        doc.render(context)

        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        response = HttpResponse(
            file_stream.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["Content-Disposition"] = f"attachment; filename=investigtion_cas_humain_{self.object.numero}.docx"
        os.remove(sub_doc_file)
        return response
