import pytest
from django.contrib.auth.models import Group
from django.test import RequestFactory

from core.constants import Domains
from core.factories import UserFactory
from seves.context_processors import domains


@pytest.mark.django_db
def test_domains_context_processor_all_domains(django_user_model, settings):
    factory = RequestFactory()
    user = UserFactory()
    sv_group, _ = Group.objects.get_or_create(name=Domains.SV.group)
    ssa_group, _ = Group.objects.get_or_create(name=Domains.SSA.group)
    user.groups.add(sv_group, ssa_group)

    request = factory.get("/")
    request.user = user

    request.domain = "sv"
    context = domains(request)
    assert context["current_domain"].nom == "Santé des végétaux"
    assert context["current_domain"].help_url == "https://doc-sv.seves.beta.gouv.fr"
    assert context["other_domains"] == [Domains.SSA, Domains.TIAC]

    request.domain = "ssa"
    context = domains(request)
    assert context["current_domain"].nom == "Sécurité sanitaire des aliments"
    assert context["other_domains"] == [Domains.SV, Domains.TIAC]
