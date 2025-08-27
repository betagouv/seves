from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.forms import Media
from django.http import Http404, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView

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
from tiac import forms
from tiac.mixins import WithFilteredListMixin
from tiac.models import EvenementSimple
from .filters import EvenementSimpleFilter
from .formsets import EtablissementFormSet


class EvenementSimpleCreationView(
    WithFormErrorsAsMessagesMixin, MediaDefiningMixin, WithAddUserContactsMixin, CreateView
):
    template_name = "tiac/evenement_simple.html"
    form_class = forms.EvenementSimpleForm

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["etablissement_formset"] = EtablissementFormSet()
        context["empty_form"] = context["etablissement_formset"].empty_form
        return context

    def get_media(self, **context_data) -> Media:
        return super().get_media(**context_data) + context_data["etablissement_formset"].media

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
        messages.success(self.request, "L’évènement a été créé avec succès.")
        return HttpResponseRedirect(self.object.get_absolute_url())

    def form_invalid(self, form):
        self.object = None
        return super().form_invalid(form)


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
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        return context


class EvenementListView(WithFilteredListMixin, ListView):
    model = EvenementSimple
    paginate_by = 100

    def get_queryset(self):
        queryset = self.apply_ordering(self.get_raw_queryset())
        self.filter = EvenementSimpleFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        for evenement in context["object_list"]:
            etat_data = evenement.get_etat_data_from_fin_de_suivi(evenement.has_fin_de_suivi)
            evenement.etat = etat_data["etat"]
            evenement.readable_etat = etat_data["readable_etat"]

        context["total_object_count"] = self.get_raw_queryset().count()

        return context
