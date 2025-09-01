import json
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.mixins import WithClotureContextMixin
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
    WithSireneTokenMixin,
)
from core.models import Export
from ssa.forms import EvenementProduitForm
from ssa.formsets import EtablissementFormSet
from ssa.models import EvenementProduit, CategorieDanger, Etablissement
from ssa.models.evenement_produit import CategorieProduit
from ssa.tasks import export_task
from .mixins import WithFilteredListMixin, EvenementProduitValuesMixin


class EvenementProduitCreateView(
    WithFormErrorsAsMessagesMixin,
    WithAddUserContactsMixin,
    WithSireneTokenMixin,
    EvenementProduitValuesMixin,
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

    def formset_invalid(self):
        self.object = None
        messages.error(
            self.request,
            "Erreurs dans le(s) formulaire(s) Etablissement",
        )
        for i, form in enumerate(self.etablissement_formset):
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(
                            self.request, f"Erreur dans le formulaire établissement #{i + 1} : '{field}': {error}"
                        )

        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not self.etablissement_formset.is_valid():
            return self.formset_invalid()

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empty_form"] = self.etablissement_formset.empty_form
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
    DetailView,
):
    model = EvenementProduit
    template_name = "ssa/evenement_produit_detail.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_queryset(self):
        return EvenementProduit.objects.all().all().select_related("createur")

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        if queryset is None:
            queryset = self.get_queryset()
        try:
            annee, numero_evenement = self.kwargs["numero"].split(".")
            self.object = queryset.get(numero_annee=annee, numero_evenement=numero_evenement)
            return self.object
        except (ValueError, EvenementProduit.DoesNotExist):
            raise Http404("Fiche produit non trouvée")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_be_deleted"] = self.get_object().can_be_deleted(self.request.user)
        context["can_publish"] = self.get_object().can_publish(self.request.user)
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        context["can_be_updated"] = self.get_object().can_be_updated(self.request.user)
        return context


class EvenementUpdateView(
    UserPassesTestMixin,
    WithAddUserContactsMixin,
    WithFormErrorsAsMessagesMixin,
    EvenementProduitValuesMixin,
    WithSireneTokenMixin,
    UpdateView,
):
    form_class = EvenementProduitForm
    template_name = "ssa/evenement_produit_form.html"

    def get_queryset(self):
        return EvenementProduit.objects.all()

    def test_func(self) -> bool | None:
        return self.get_object().can_be_updated(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Etablissement.objects.for_object(self.get_object())
        formset = EtablissementFormSet(instance=self.get_object(), queryset=queryset)
        context["empty_form"] = formset.empty_form
        context["formset"] = formset
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.add_user_contacts(form.instance)
        return response

    def post(self, request, pk):
        self.object = self.get_object()
        form = self.get_form()
        queryset = Etablissement.objects.for_object(self.get_object())
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
            self.object = form.save()
            formset.save()
            self.add_user_contacts(self.object)
        messages.success(self.request, "L'événement produit a bien été modifié.")
        return HttpResponseRedirect(self.get_success_url())


class EvenementProduitListView(WithFilteredListMixin, ListView):
    model = EvenementProduit
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter
        context["categorie_produit_data"] = json.dumps(CategorieProduit.build_options())
        context["categorie_danger_data"] = json.dumps(CategorieDanger.build_options(sorted_results=True))

        for evenement in context["object_list"]:
            etat_data = evenement.get_etat_data_from_fin_de_suivi(evenement.has_fin_de_suivi)
            evenement.etat = etat_data["etat"]
            evenement.readable_etat = etat_data["readable_etat"]

        context["total_object_count"] = self.get_raw_queryset().count()
        return context


class EvenementProduitExportView(WithFilteredListMixin, View):
    http_method_names = ["post"]

    def post(self, request):
        ids = list(self.get_queryset().values_list("id", flat=True))
        task = Export.objects.create(object_ids=ids, user=request.user)
        export_task.delay(task.id)
        messages.success(
            request, "Votre demande d'export a bien été enregistrée, vous receverez un mail quand le fichier sera prêt."
        )
        allowed_keys = list(self.filter.get_filters().keys()) + ["order_by", "order_dir"]
        allowed_params = {k: v for k, v in request.GET.items() if k in allowed_keys}
        return HttpResponseRedirect(f"{reverse('ssa:evenement-produit-liste')}?{urlencode(allowed_params)}")
