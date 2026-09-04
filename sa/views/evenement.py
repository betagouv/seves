from functools import cached_property

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.forms import Media
from django.http import Http404, HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.edit import ModelFormMixin, ProcessFormView

from core.mixins import MediaDefiningMixin, WithFormErrorsAsMessagesMixin, WithFormsetInvalidMixin
from sa.forms.evenement import EvenementAnimalForm
from sa.formsets import AnalyseFormSet
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


class EvenementAnimalBaseView(
    WithFormErrorsAsMessagesMixin,
    MediaDefiningMixin,
    WithFormsetInvalidMixin,
    ModelFormMixin,
    ProcessFormView,
):
    template_name = "sa/evenement_animal_form.html"
    form_class = EvenementAnimalForm
    model = EvenementAnimal

    @cached_property
    def analyse_formset(self):
        return AnalyseFormSet(**self.get_analyse_formset_kwargs())

    def get_analyse_formset_kwargs(self):
        kwargs = {"form_kwargs": {"maladie_initial": self.request.GET.get("maladie")}}
        if self.object:
            kwargs["instance"] = self.object
        if self.request.POST:
            kwargs["data"] = self.request.POST
        return kwargs

    def get_object(self, queryset=None):
        if not self.kwargs.get(self.pk_url_kwarg):
            return None
        return super().get_object(queryset)

    def get_media(self, **context_data) -> Media:
        return context_data["form"].media + self.analyse_formset.media

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["analyse_formset"] = self.analyse_formset
        return context

    def post(self, request, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()

        if not self.analyse_formset.is_valid():
            return self.formset_invalid(
                self.analyse_formset,
                "Erreurs dans le(s) formulaire(s) Analyse",
                "Erreur dans le formulaire analyse",
            )

        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)
        return self.form_valid(form)

    def form_valid(self, form):
        self.object = form.save()
        self.analyse_formset.instance = self.object
        self.analyse_formset.save()
        return HttpResponseRedirect(self.object.get_absolute_url())


class EvenementAnimalCreationView(EvenementAnimalBaseView, CreateView):
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


class EvenementAnimalDetailsView(UserPassesTestMixin, DetailView):
    model = EvenementAnimal
    template_name = "sa/evenement_animal_details.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_queryset(self):
        return EvenementAnimal.objects.all()

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        if queryset is None:
            queryset = self.get_queryset()
        try:
            self.object = queryset.get(pk=self.kwargs["pk"])
            return self.object
        except (ValueError, EvenementAnimal.DoesNotExist):
            raise Http404("Fiche non trouvée")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.request.user.agent.structure.contact_set.get()
        context["etat"] = self.object.get_etat_data_for_contact(contact)
        context["can_publish"] = self.get_object().can_publish(self.request.user)
        context["content_type"] = ContentType.objects.get_for_model(self.object)
        context["latest_version"] = self.object.latest_version
        context["can_be_deleted"] = self.get_object().can_be_deleted(self.request.user)
        return context
