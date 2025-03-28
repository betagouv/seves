from django.http import HttpResponseRedirect, Http404
from django.views.generic import CreateView, DetailView

from core.mixins import WithEtatMixin, WithFormErrorsAsMessagesMixin
from ssa.forms import EvenementProduitForm
from ssa.models import EvenementProduit
from django.contrib import messages


class EvenementProduitCreateView(WithFormErrorsAsMessagesMixin, CreateView):
    form_class = EvenementProduitForm
    template_name = "ssa/evenement_produit_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        if self.request.POST.get("action") == "publish":
            self.object.etat = WithEtatMixin.Etat.EN_COURS
        self.object.createur = self.request.user.agent.structure
        self.object.save()
        messages.success(self.request, "La fiche produit a été créé avec succès.")
        return HttpResponseRedirect(self.object.get_absolute_url())


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
