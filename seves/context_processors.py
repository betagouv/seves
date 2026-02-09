from django.conf import settings
from django.urls import reverse_lazy

from core.constants import Domains


def common_settings(request):
    return {
        "COMMUNES_API": settings.COMMUNES_API,
        "siret_api_endpoint": reverse_lazy("siret-api", kwargs={"siret": "__siret__"}),
        "env": settings.ENVIRONMENT,
    }


def select_empty_choice(request):
    return {"select_empty_choice": settings.SELECT_EMPTY_CHOICE}


def environment_class(request):
    match settings.ENVIRONMENT:
        case "recette":
            return {"environment_class": "environment-banner environment-recette"}
        case "dev":
            return {"environment_class": "environment-banner environment-dev"}
        case "test":
            return {"environment_class": "environment-banner environment-test"}
        case "preprod":
            return {"environment_class": "environment-banner environment-preprod"}
        case _:
            return {"environment_class": ""}


def domains(request):
    user_groups = [g.name for g in request.user.groups.all()]

    current_domain = None
    other_domains = []
    if hasattr(request, "domain"):
        for domain in Domains:
            if request.domain == domain.value:
                current_domain = domain
            elif domain.group in user_groups:
                other_domains.append(domain)

    return {"current_domain": current_domain, "other_domains": other_domains}
