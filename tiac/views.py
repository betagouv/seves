from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.views.generic import CreateView, DetailView, ListView

from core.mixins import WithFormErrorsAsMessagesMixin, WithFreeLinksListInContextMixin
from core.views import MediaDefiningMixin
from tiac import forms
from tiac.mixins import WithFilteredListMixin
from tiac.models import EvenementSimple
from .filters import EvenementSimpleFilter


class EvenementSimpleCreationView(WithFormErrorsAsMessagesMixin, SuccessMessageMixin, MediaDefiningMixin, CreateView):
    template_name = "tiac/evenement_simple.html"
    form_class = forms.EvenementSimpleForm
    success_message = "L’évènement a été créé avec succès."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return self.object.get_absolute_url()


class EvenementSimpleDetailView(
    UserPassesTestMixin,
    WithFreeLinksListInContextMixin,
    DetailView,
):
    model = EvenementSimple
    template_name = "tiac/evenement_simple_detail.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_queryset(self):
        return EvenementSimple.objects.all().select_related("createur")

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
