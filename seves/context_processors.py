from django.conf import settings
from django.urls import reverse_lazy

from core.constants import Domains


def common_settings(request):
    return {
        "COMMUNES_API": settings.COMMUNES_API,
        "GEO_API_ROOT": settings.GEO_API_ROOT,
        "REVERSE_GEO_API": settings.REVERSE_GEO_API,
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


def notice(request):
    domain = getattr(request, "domain", None)
    if settings.ALIM_NOTICE_ENABLED and domain in (Domains.SSA.value, Domains.TIAC.value):
        return {
            "notice": {
                "id": settings.ALIM_NOTICE_VERSION,
                "can_be_closed": settings.ALIM_NOTICE_CAN_BE_CLOSED,
                "html": settings.ALIM_NOTICE_HTML,
            }
        }
    if settings.SV_NOTICE_ENABLED and domain == Domains.SV.value:
        return {
            "notice": {
                "id": settings.SV_NOTICE_VERSION,
                "can_be_closed": settings.SV_NOTICE_CAN_BE_CLOSED,
                "html": settings.SV_NOTICE_HTML,
            }
        }
    if settings.SA_NOTICE_ENABLED and domain == Domains.SA.value:
        return {
            "notice": {
                "id": settings.SA_NOTICE_VERSION,
                "can_be_closed": settings.SA_NOTICE_CAN_BE_CLOSED,
                "html": settings.SA_NOTICE_HTML,
            }
        }
    return {}
