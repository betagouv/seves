from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.views.generic import CreateView, DetailView

from core.mixins import WithFormErrorsAsMessagesMixin
from tiac import forms
from tiac.models import EvenementSimple


class EvenementSimpleCreationView(WithFormErrorsAsMessagesMixin, SuccessMessageMixin, CreateView):
    template_name = "tiac/evenement_simple.html"
    form_class = forms.EvenementSimpleForm
    success_message = "L’évènement a été créé avec succès."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        # TODO add success message
        return self.object.get_absolute_url()


class EvenementSimpleDetailView(
    UserPassesTestMixin,
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
