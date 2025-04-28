from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, Http404
from django.views.generic import CreateView, DetailView, ListView

from core.mixins import WithFormErrorsAsMessagesMixin, WithFreeLinksListInContextMixin
from ssa.forms import EvenementProduitForm
from ssa.formsets import EtablissementFormSet
from ssa.models import EvenementProduit
from ssa.filters import EvenementProduitFilter


class EvenementProduitCreateView(WithFormErrorsAsMessagesMixin, CreateView):
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

        messages.success(self.request, "La fiche produit a été créé avec succès.")
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empty_form"] = self.etablissement_formset.empty_form
        context["formset"] = self.etablissement_formset
        return context


class EvenementProduitDetailView(WithFreeLinksListInContextMixin, UserPassesTestMixin, DetailView):
    model = EvenementProduit
    template_name = "ssa/evenement_produit_detail.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_queryset(self):
        return EvenementProduit.objects.all().select_related("createur")

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
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        return context


class EvenementProduitListView(ListView):
    model = EvenementProduit
    paginate_by = 100

    def get_queryset(self):
        user = self.request.user
        contact = user.agent.structure.contact_set.get()
        queryset = (
            EvenementProduit.objects.select_related("createur")
            .get_user_can_view(user)
            .with_fin_de_suivi(contact)
            .with_nb_liens_libres()
            .order_by_numero()
        )
        self.filter = EvenementProduitFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter

        for evenement in context["object_list"]:
            etat_data = evenement.get_etat_data_from_fin_de_suivi(evenement.has_fin_de_suivi)
            evenement.etat = etat_data["etat"]
            evenement.readable_etat = etat_data["readable_etat"]
        return context
