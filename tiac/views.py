import json

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.forms import Media
from django.http import Http404
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.edit import ProcessFormView

from core.mixins import (
    WithFormErrorsAsMessagesMixin,
    WithFreeLinksListInContextMixin,
    WithClotureContextMixin,
    WithBlocCommunPermission,
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithMessageMixin,
    WithContactFormsInContextMixin,
    WithContactListInContextMixin,
    WithAddUserContactsMixin,
)
from core.views import MediaDefiningMixin
from ssa.models import CategorieDanger, CategorieProduit
from tiac import forms
from tiac.mixins import WithFilteredListMixin
from tiac.models import EvenementSimple, InvestigationTiac
from .constants import DangersSyndromiques
from .display import DisplayItem
from .filters import TiacFilter
from .forms import EvenementSimpleTransferForm
from .formsets import (
    EvenementSimpleEtablissementFormSet,
    RepasFormSet,
    AlimentFormSet,
    InvestigationTiacEtablissementFormSet,
    AnalysesAlimentairesFormSet,
)


class EvenementSimpleManipulationMixin(
    WithFormErrorsAsMessagesMixin, WithAddUserContactsMixin, MediaDefiningMixin, ProcessFormView
):
    template_name = "tiac/evenement_simple.html"
    form_class = forms.EvenementSimpleForm
    etablissement_formset_class = EvenementSimpleEtablissementFormSet

    def get_media(self, **context_data) -> Media:
        return super().get_media(**context_data) + context_data["etablissement_formset"].media

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_etablissement_formset_kwargs(self):
        kwargs = {}
        if self.request.method in ("POST", "PUT"):
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs

    def get_etablissement_formset(self):
        if not hasattr(self, "etablissement_formset"):
            self.etablissement_formset = self.etablissement_formset_class(**self.get_etablissement_formset_kwargs())
        return self.etablissement_formset

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_success_message(self):
        return (
            "L’évènement a été publié avec succès."
            if self.object.is_published
            else "L’évènement a été créé avec succès."
        )

    def form_valid(self, form):
        self.object = form.save()
        self.get_etablissement_formset().instance = self.object
        self.get_etablissement_formset().save()

        self.add_user_contacts(self.object)
        messages.success(self.request, self.get_success_message())
        return super().form_valid(form)

    def formset_invalid(self):
        self.object = None
        messages.error(
            self.request,
            "Erreurs dans le(s) formulaire(s) Etablissement",
        )
        for i, form in enumerate(self.get_etablissement_formset()):
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(
                            self.request, f"Erreur dans le formulaire établissement #{i + 1} : '{field}': {error}"
                        )

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["etablissement_formset"] = self.get_etablissement_formset()
        return context

    def post(self, request, *args, **kwargs):
        if not self.get_etablissement_formset().is_valid():
            return self.formset_invalid()
        return super().post(request, *args, **kwargs)


class EvenementSimpleCreationView(EvenementSimpleManipulationMixin, CreateView):
    def form_invalid(self, form):
        self.object = None
        return super().form_invalid(form)


class EvenementSimpleUpdateView(UserPassesTestMixin, EvenementSimpleManipulationMixin, UpdateView):
    model = EvenementSimple
    template_name = "tiac/evenement_simple_modification.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_success_message(self):
        return "L’évènement a été mis à jour avec succès."

    def get_etablissement_formset_kwargs(self):
        return {**super().get_etablissement_formset_kwargs(), "instance": self.get_object()}


class EvenementSimpleDetailView(
    UserPassesTestMixin,
    WithFreeLinksListInContextMixin,
    WithClotureContextMixin,
    WithBlocCommunPermission,
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithMessageMixin,
    WithContactFormsInContextMixin,
    WithContactListInContextMixin,
    DetailView,
):
    model = EvenementSimple
    template_name = "tiac/evenement_simple_detail.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_queryset(self):
        return (
            EvenementSimple.objects.all()
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
            annee, numero_evenement = self.kwargs["numero"].split(".")
            self.object = queryset.get(numero_annee=annee, numero_evenement=numero_evenement)
            return self.object
        except (ValueError, EvenementSimple.DoesNotExist):
            raise Http404("Fiche produit non trouvée")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_be_deleted"] = self.get_object().can_be_deleted(self.request.user)
        context["can_publish"] = self.get_object().can_publish(self.request.user)
        context["can_be_modified"] = self.get_object().can_be_modified(self.request.user)
        context["can_be_transfered"] = self.get_object().can_be_transfered(self.request.user)
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        context["transfer_form"] = EvenementSimpleTransferForm()
        context["etablissements"] = self.get_object().etablissements.all()
        return context


class TiacListView(WithFilteredListMixin, MediaDefiningMixin, ListView):
    paginate_by = 100
    context_object_name = "objects"

    def get_template_names(self):
        return ["tiac/tiac_list.html"]

    def get_media(self, **context_data) -> Media:
        return context_data["filter"].form.media if "filter" in context_data else Media()

    def get_queryset(self):
        queryset = self.apply_ordering(self.get_raw_queryset)
        self.filter = TiacFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object_list = []
        for evenement in context["object_list"]:
            etat_data = evenement.get_etat_data_from_fin_de_suivi(evenement.has_fin_de_suivi)
            evenement.etat = etat_data["etat"]
            evenement.readable_etat = etat_data["readable_etat"]
            object_list.append(DisplayItem.from_object(evenement))

        context["total_object_count"] = self.get_raw_queryset.count()
        context["object_list"] = object_list
        context["filter"] = self.filter
        context["categorie_produit_data"] = json.dumps(CategorieProduit.build_options())
        context["categorie_danger_data"] = json.dumps(CategorieDanger.build_options(sorted_results=True))
        return context


class EvenementSimpleTransferView(UpdateView):
    form_class = EvenementSimpleTransferForm

    def get_queryset(self):
        return EvenementSimple.objects.all()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"L’évènement a bien été transféré à la {self.object.transfered_to}")
        self.object.contacts.add(self.object.transfered_to.contact_set.get())
        return response


class InvestigationTiacCreationView(
    WithFormErrorsAsMessagesMixin, MediaDefiningMixin, WithAddUserContactsMixin, CreateView
):
    template_name = "tiac/investigation.html"
    form_class = forms.InvestigationTiacForm

    def dispatch(self, request, *args, **kwargs):
        if self.request.POST:
            self.repas_formset = RepasFormSet(data=self.request.POST)
            self.aliment_formset = AlimentFormSet(data=self.request.POST)
        else:
            self.repas_formset = RepasFormSet()
            self.aliment_formset = AlimentFormSet()

        self.etablissement_formset = self.get_etablissement_formset()
        self.analyse_alimentaire_formset = self.get_analyse_alimentaire_formset()
        return super().dispatch(request, *args, **kwargs)

    def get_media(self, **context_data) -> Media:
        media = super().get_media(**context_data)
        for key, value in context_data.items():
            if key.endswith("formset"):
                media += value.media
        return media

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_etablissement_formset(self):
        kwargs = {"title_level": "h4", "title_classes": "fr-h5"}
        if hasattr(self, "object"):
            kwargs.update({"instance": self.object})
        if self.request.POST:
            kwargs["data"] = self.request.POST

        return InvestigationTiacEtablissementFormSet(**kwargs)

    def get_analyse_alimentaire_formset(self):
        kwargs = {}
        if hasattr(self, "object"):
            kwargs.update({"instance": self.object})
        if self.request.POST:
            kwargs["data"] = self.request.POST

        return AnalysesAlimentairesFormSet(**kwargs)

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dangers"] = DangersSyndromiques.as_list()
        context["dangers_json"] = json.dumps([choice.to_dict() for choice in DangersSyndromiques.as_list()])
        context["repas_formset"] = RepasFormSet()
        context["aliment_formset"] = AlimentFormSet()
        context["empty_repas_form"] = context["repas_formset"].empty_form
        context["empty_aliment_form"] = context["aliment_formset"].empty_form
        context["etablissement_formset"] = self.etablissement_formset
        context["analyse_alimentaire_formset"] = self.analyse_alimentaire_formset
        context["categorie_danger_data"] = json.dumps(CategorieDanger.build_options(sorted_results=True))
        context["danger_plus_courant"] = InvestigationTiac.danger_plus_courants()
        return context

    def formset_invalid(self, formset, msg_1, msg_2):
        self.object = None
        messages.error(self.request, msg_1)
        for i, form in enumerate(formset):
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(self.request, f"{msg_2} #{i + 1} : '{field}': {error}")

        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        if not self.repas_formset.is_valid():
            return self.formset_invalid(
                self.repas_formset, "Erreurs dans le(s) formulaire(s) Repas", "Erreur dans le formulaire repas"
            )

        if not self.aliment_formset.is_valid():
            return self.formset_invalid(
                self.aliment_formset, "Erreurs dans le(s) formulaire(s) Aliments", "Erreur dans le formulaire aliment"
            )

        if not self.etablissement_formset.is_valid():
            return self.formset_invalid(
                self.etablissement_formset,
                "Erreurs dans le(s) formulaire(s) Établissements",
                "Erreur dans le formulaire établissement",
            )

        if not self.analyse_alimentaire_formset.is_valid():
            return self.formset_invalid(
                self.analyse_alimentaire_formset,
                "Erreurs dans le(s) formulaire(s) Analyses alimentaires",
                "Erreur dans le formulaire analyses alimentaires",
            )

        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)
        return self.form_valid(form)

    def form_valid(self, form):
        self.object = form.save()
        self.repas_formset.instance = self.object
        self.repas_formset.save()
        self.aliment_formset.instance = self.object
        self.aliment_formset.save()
        self.etablissement_formset.instance = self.object
        self.etablissement_formset.save()
        self.analyse_alimentaire_formset.instance = self.object
        self.analyse_alimentaire_formset.save()
        self.add_user_contacts(self.object)

        if self.object.is_published:
            messages.success(self.request, "L’évènement a été publié avec succès.")
        else:
            messages.success(self.request, "L’évènement a été créé avec succès.")
        return HttpResponseRedirect(self.object.get_absolute_url())


class InvestigationTiacDetailView(
    UserPassesTestMixin,
    WithFreeLinksListInContextMixin,
    WithClotureContextMixin,
    WithBlocCommunPermission,
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithMessageMixin,
    WithContactFormsInContextMixin,
    WithContactListInContextMixin,
    DetailView,
):
    model = InvestigationTiac
    template_name = "tiac/investigation_tiac_detail.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_queryset(self):
        return (
            InvestigationTiac.objects.all()
            .select_related("createur")
            .prefetch_related("repas__departement", "documents")
        )

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        if queryset is None:
            queryset = self.get_queryset()
        try:
            annee, numero_evenement = self.kwargs["numero"].split(".")
            self.object = queryset.get(numero_annee=annee, numero_evenement=numero_evenement)
            return self.object
        except (ValueError, EvenementSimple.DoesNotExist):
            raise Http404("Fiche produit non trouvée")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_publish"] = self.get_object().can_publish(self.request.user)
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        context["can_be_deleted"] = self.get_object().can_be_deleted(self.request.user)
        context["dangers"] = [
            d.to_dict() for d in DangersSyndromiques.as_list() if d.value in self.object.danger_syndromiques_suspectes
        ]
        context["etablissements"] = self.get_object().etablissements.all()
        context["raisons_sociales"] = [e.raison_sociale for e in context["etablissements"]]
        context["communes"] = [e.commune for e in context["etablissements"] if e.commune]
        context["dates_repas"] = [
            r.datetime_repas.strftime("%d/%m/%Y %Hh%M") for r in self.get_object().repas.all() if r.datetime_repas
        ]
        return context

    def get_publish_success_message(self):
        return "L’évènement a été publié avec succès."
