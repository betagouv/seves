import pytest
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.urls import reverse

from core.factories import UserFactory
from seves.context_processors import domains


@pytest.mark.django_db
def test_domains_context_processor_all_domains(django_user_model, settings):
    factory = RequestFactory()
    user = UserFactory()
    sv_group, _ = Group.objects.get_or_create(name=settings.SV_GROUP)
    ssa_group, _ = Group.objects.get_or_create(name=settings.SSA_GROUP)
    user.groups.add(sv_group, ssa_group)

    request = factory.get("/")
    request.user = user

    request.domain = "sv"
    context = domains(request)
    assert context["current_domain"]["nom"] == "Santé des végétaux"
    assert context["other_domains"] == [
        {
            "icon": "fr-icon-restaurant-line ",
            "nom": "Sécurité sanitaire des aliments",
            "url": reverse("ssa:evenement-produit-liste"),
        },
    ]

    request.domain = "ssa"
    context = domains(request)
    assert context["current_domain"]["nom"] == "Sécurité sanitaire des aliments"
    assert context["other_domains"] == [
        {
            "icon": "fr-icon-leaf-line",
            "nom": "Santé des végétaux",
            "url": reverse("sv:evenement-liste"),
        }
    ]
