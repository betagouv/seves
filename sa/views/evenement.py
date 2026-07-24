from django.http import Http404
from django.views.generic import CreateView, DetailView, ListView

from core.mixins import WithFormErrorsAsMessagesMixin
from sa.forms.evenement import EvenementAnimalForm
from sa.models import Espece, EvenementAnimal, Maladie
from sa.models.evenement import StatutAnimal


class EvenementListView(ListView):
    paginate_by = 100
    context_object_name = "objects"
    model = EvenementAnimal


class EvenementAnimalCreationView(WithFormErrorsAsMessagesMixin, CreateView):
    form_class = EvenementAnimalForm
    template_name = "sa/evenement_animal_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["maladie"] = self.request.GET.get("maladie")
        kwargs["espece"] = self.request.GET.get("espece")
        kwargs["statut_animal"] = self.request.GET.get("statut_animal")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["maladie"] = Maladie.objects.get(pk=self.request.GET.get("maladie"))
        context["espece"] = Espece.objects.get(pk=self.request.GET.get("espece"))
        context["statut_animal"] = StatutAnimal(self.request.GET.get("statut_animal"))
        return context


class EvenementAnimalDetailsView(DetailView):
    model = EvenementAnimal
    template_name = "sa/evenement_animal_details.html"

    def get_queryset(self):
        return EvenementAnimal.objects.all()

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        if queryset is None:
            queryset = self.get_queryset()
        try:
            annee, numero_evenement = self.kwargs["numero"].split(".")
            self.object = queryset.get(numero_annee=annee, numero_evenement=numero_evenement)
            return self.object
        except (ValueError, EvenementAnimal.DoesNotExist):
            raise Http404("Fiche non trouvée")
