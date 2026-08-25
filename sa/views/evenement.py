from django.contrib.contenttypes.models import ContentType
from django.forms import Media
from django.http import Http404
from django.views.generic import CreateView, DetailView, ListView

from core.mixins import MediaDefiningMixin, WithFormErrorsAsMessagesMixin
from sa.forms.evenement import EvenementAnimalForm
from sa.models import Espece, EvenementAnimal, Maladie
from sa.models.evenement import StatutAnimal

from .mixins import WithFilteredListMixin


class EvenementListView(WithFilteredListMixin, MediaDefiningMixin, ListView):
    model = EvenementAnimal
    paginate_by = 100

    def get_media(self, **context_data) -> Media:
        return context_data["filter"].form.media if "filter" in context_data else Media()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter
        context["total_object_count"] = self.get_raw_queryset().count()

        for evenement in context["evenementanimal_list"]:
            etat_data = evenement.get_etat_data_from_fin_de_suivi(evenement.has_fin_de_suivi)
            evenement.etat = etat_data["etat"]
            evenement.readable_etat = etat_data["readable_etat"]

        return context


class EvenementAnimalCreationView(WithFormErrorsAsMessagesMixin, MediaDefiningMixin, CreateView):
    form_class = EvenementAnimalForm
    template_name = "sa/evenement_animal_form.html"

    def get_media(self, **context_data):
        return context_data["form"].media

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["maladie"] = self.request.GET.get("maladie")
        kwargs["espece"] = self.request.GET.get("espece")
        kwargs["statut_animal"] = self.request.GET.get("statut_animal")
        kwargs["structure"] = self.request.user.agent.structure
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.request.user.agent.structure.contact_set.get()
        context["etat"] = self.object.get_etat_data_for_contact(contact)
        context["content_type"] = ContentType.objects.get_for_model(self.object)
        context["latest_version"] = self.object.latest_version
        return context
