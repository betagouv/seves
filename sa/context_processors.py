from django.urls import resolve

from sa.apps import SaConfig
from sa.forms.evenement import EvenementAnimalPreCreationForm


def pre_creation_form(request):
    match = resolve(request.path)
    if match.app_name != SaConfig.name:
        return {}

    return {"pre_creation_form": EvenementAnimalPreCreationForm()}
