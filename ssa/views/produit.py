from django.http import HttpResponseRedirect, Http404
from django.views.generic import CreateView, DetailView

from core.mixins import WithEtatMixin, WithFormErrorsAsMessagesMixin
from ssa.forms import EvenementProduitForm
from ssa.models import EvenementProduit
from django.contrib import messages
from ssa.formsets import EtablissementFormSet


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
        self.object = form.save(commit=False)
        if self.request.POST.get("action") == "publish":
            self.object.etat = WithEtatMixin.Etat.EN_COURS
        self.object.createur = self.request.user.agent.structure
        self.object.save()

        self.etablissement_formset.instance = self.object
        self.etablissement_formset.save()

        messages.success(self.request, "La fiche produit a été créé avec succès.")
        return HttpResponseRedirect(self.object.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empty_form"] = self.etablissement_formset.empty_form
        context["formset"] = self.etablissement_formset
        return context


class EvenementProduitDetailView(DetailView):
    model = EvenementProduit
    template_name = "ssa/evenement_produit_detail.html"

    def get_queryset(self):
        return EvenementProduit.objects.all()

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        if queryset is None:
            queryset = self.get_queryset()
        try:
            annee, numero_evenement = self.kwargs["numero"].split("-")
            self.object = queryset.get(numero_annee=annee, numero_evenement=numero_evenement)
            return self.object
        except (ValueError, EvenementProduit.DoesNotExist):
            raise Http404("Fiche produit non trouvée")
