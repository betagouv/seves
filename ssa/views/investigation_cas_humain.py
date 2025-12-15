from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.forms import Media
from django.http import Http404, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, UpdateView

from core.mixins import (
    WithAddUserContactsMixin,
    WithBlocCommunPermission,
    WithClotureContextMixin,
    WithContactFormsInContextMixin,
    WithContactListInContextMixin,
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithFinDeSuiviMixin,
    WithFormErrorsAsMessagesMixin,
    WithFreeLinksListInContextMixin,
    WithMessageMixin,
)
from core.views import MediaDefiningMixin

from ..forms import InvestigationCasHumainForm
from ..formsets import InvestigationCasHumainsEtablissementFormSet
from ..models import EvenementInvestigationCasHumain
from .mixins import EvenementProduitValuesMixin


class InvestigationCasHumainCreateView(
    WithFormErrorsAsMessagesMixin,
    WithAddUserContactsMixin,
    EvenementProduitValuesMixin,
    MediaDefiningMixin,
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


class InvestigationCasHumainUpdateView(InvestigationCasHumainCreateView, UpdateView):
    success_message = "La fiche d'investigation cas humain a été mise à jour avec succès."

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
