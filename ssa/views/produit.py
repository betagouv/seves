import io
import datetime
import json
import os

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.forms import Media
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from docxtpl import DocxTemplate
from reversion.models import Version

from core.mixins import (
    WithClotureContextMixin,
    WithDocumentExportContextMixin,
    WithFinDeSuiviMixin,
    WithFormsetInvalidMixin,
    MediaDefiningMixin,
)
from core.mixins import (
    WithFormErrorsAsMessagesMixin,
    WithFreeLinksListInContextMixin,
    WithMessageMixin,
    WithContactListInContextMixin,
    WithDocumentUploadFormMixin,
    WithDocumentListInContextMixin,
    WithContactFormsInContextMixin,
    WithBlocCommunPermission,
    WithAddUserContactsMixin,
)
from ssa.forms import EvenementProduitForm
from ssa.formsets import EtablissementFormSet
from ssa.models import EvenementProduit, Etablissement
from ..constants import CategorieDanger, CategorieProduit, TypeEvenement
from .mixins import WithFilteredListMixin, EvenementProduitValuesMixin
from ..display import EvenementDisplay
from ..notifications import notify_type_evenement_fna, notify_souches_clusters, notify_alimentation_animale


class EvenementProduitCreateView(
    WithFormErrorsAsMessagesMixin,
    WithAddUserContactsMixin,
    EvenementProduitValuesMixin,
    MediaDefiningMixin,
    WithFormsetInvalidMixin,
    CreateView,
):
    form_class = EvenementProduitForm
    template_name = "ssa/evenement_produit_form.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.POST:
            self.etablissement_formset = EtablissementFormSet(data=self.request.POST)
        else:
            self.etablissement_formset = EtablissementFormSet()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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

    def form_valid(self, form):
        self.object = form.save()
        self.etablissement_formset.instance = self.object
        self.etablissement_formset.save()
        self.add_user_contacts(self.object)

        messages.success(self.request, "La fiche produit a été créée avec succès.")
        return HttpResponseRedirect(self.object.get_absolute_url())

    def form_invalid(self, form):
        self.object = None
        return super().form_invalid(form)

    def get_media(self, **context_data) -> Media:
        return super().get_media(**context_data) + context_data["formset"].media

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = self.etablissement_formset
        return context


class EvenementProduitDetailView(
    WithBlocCommunPermission,
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithMessageMixin,
    WithContactFormsInContextMixin,
    WithContactListInContextMixin,
    WithFreeLinksListInContextMixin,
    WithClotureContextMixin,
    UserPassesTestMixin,
    WithFinDeSuiviMixin,
    DetailView,
):
    model = EvenementProduit
    template_name = "ssa/evenement_produit_detail.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_queryset(self):
        return EvenementProduit.objects.with_departement_prefetched().all().select_related("createur")

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        if queryset is None:
            queryset = self.get_queryset()
        try:
            self.object = queryset.get(pk=self.kwargs["pk"])
            return self.object
        except (ValueError, EvenementProduit.DoesNotExist):
            raise Http404("Fiche produit non trouvée")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.request.user.agent.structure.contact_set.all()[0]
        context["etat"] = self.get_object().get_etat_data_for_contact(contact)
        context["can_be_deleted"] = self.get_object().can_be_deleted(self.request.user)
        context["can_publish"] = self.get_object().can_publish(self.request.user)
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        context["can_be_updated"] = self.get_object().can_be_updated(self.request.user)
        context["can_be_downloaded"] = self.get_object().can_be_downloaded(self.request.user)
        return context


class EvenementUpdateView(
    UserPassesTestMixin,
    WithAddUserContactsMixin,
    WithFormErrorsAsMessagesMixin,
    EvenementProduitValuesMixin,
    MediaDefiningMixin,
    UpdateView,
):
    form_class = EvenementProduitForm
    template_name = "ssa/evenement_produit_form.html"

    def get_queryset(self):
        return EvenementProduit.objects.all()

    def test_func(self) -> bool | None:
        return self.get_object().can_be_updated(self.request.user)

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        self.object = super().get_object(queryset)
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["latest_version"] = Version.objects.get_for_object(self.get_object()).first().pk
        return kwargs

    def get_media(self, **context_data) -> Media:
        return super().get_media(**context_data) + context_data["formset"].media

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Etablissement.objects.filter(evenement_produit=self.get_object())
        formset = EtablissementFormSet(instance=self.get_object(), queryset=queryset)
        context["formset"] = formset
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.add_user_contacts(form.instance)
        return response

    def _trigger_notifications(self):
        dirty_fields = self.object.get_dirty_fields()
        if "type_evenement" in dirty_fields and self.object.type_evenement == TypeEvenement.ALERTE_PRODUIT_NATIONALE:
            notify_type_evenement_fna(self.object, self.request.user)
        if "aliments_animaux" in dirty_fields and self.object.aliments_animaux is True:
            notify_alimentation_animale(self.object)
        if ("reference_souches" in dirty_fields) or ("reference_clusters" in dirty_fields):
            notify_souches_clusters(self.object, self.request.user)

    def post(self, request, pk):
        self.object = self.get_object()
        form = self.get_form()
        queryset = Etablissement.objects.filter(evenement_produit=self.get_object())
        formset = EtablissementFormSet(request.POST, instance=self.get_object(), queryset=queryset)
        if not form.is_valid():
            return self.form_invalid(form)

        if not formset.is_valid():
            messages.error(
                self.request,
                "Erreurs dans le(s) formulaire(s) Etablissement",
            )
            for i, form in enumerate(formset):
                if not form.is_valid():
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(
                                self.request, f"Erreur dans le formulaire établissement #{i + 1} : '{field}': {error}"
                            )

            return self.render_to_response(self.get_context_data(formset=formset))

        with transaction.atomic():
            self.object = form.save(commit=False)
            self._trigger_notifications()
            self.object.save()
            formset.save()
            self.add_user_contacts(self.object)

        messages.success(self.request, "L'événement produit a bien été modifié.")
        return HttpResponseRedirect(self.get_success_url())


class EvenementsListView(WithFilteredListMixin, ListView):
    template_name = "ssa/evenements_list.html"
    model = EvenementProduit
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter
        context["categorie_produit_data"] = json.dumps(CategorieProduit.build_options())
        context["categorie_danger_data"] = json.dumps(CategorieDanger.build_options(sorted_results=True))

        context["total_object_count"] = self.get_raw_queryset().count()
        context["object_list"] = [EvenementDisplay.from_evenement(evenement) for evenement in context["object_list"]]

        return context


class EvenementProduitDocumentExportView(WithDocumentExportContextMixin, UserPassesTestMixin, View):
    http_method_names = ["post"]

    def dispatch(self, request, pk, *args, **kwargs):
        self.object = EvenementProduit.objects.get(pk=pk)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        doc = DocxTemplate("ssa/doc_templates/evenement_produit.docx")
        sub_doc_file = self.create_document_bloc_commun()
        sub_doc = doc.new_subdoc(sub_doc_file)

        context = {
            "object": self.object,
            "free_links": self.get_free_links_numbers(),
            "bloc_commun": sub_doc,
            "now": datetime.datetime.now(),
        }
        doc.render(context)

        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        response = HttpResponse(
            file_stream.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["Content-Disposition"] = f"attachment; filename=evenement_produit_{self.object.numero}.docx"
        os.remove(sub_doc_file)
        return response

    def test_func(self):
        return self.object.can_user_access(self.request.user)
