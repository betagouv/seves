from django.urls import Resolver404, resolve

from sa.apps import SaConfig
from sa.forms.evenement import EvenementAnimalPreCreationForm


def pre_creation_form(request):
    try:
        match = resolve(request.path)
    except Resolver404:
        return {}
    if match.app_name != SaConfig.name:
        return {}
    return {"pre_creation_form": EvenementAnimalPreCreationForm(auto_id="id_pre_creation_%s")}
