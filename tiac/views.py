from django.views.generic import CreateView

from tiac import forms


class EvenementSimpleCreationView(CreateView):
    template_name = "tiac/evenement_simple.html"
    form_class = forms.EvenementSimpleForm
