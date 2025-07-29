from django.urls import reverse
from django.views.generic import CreateView

from core.mixins import WithFormErrorsAsMessagesMixin
from tiac import forms


class EvenementSimpleCreationView(WithFormErrorsAsMessagesMixin, CreateView):
    template_name = "tiac/evenement_simple.html"
    form_class = forms.EvenementSimpleForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("tiac:evenement-liste")
