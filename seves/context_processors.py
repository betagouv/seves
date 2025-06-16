from django.conf import settings
from django.urls import reverse_lazy


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
    sv_domain = {
        "icon": "fr-icon-leaf-line",
        "nom": "Santé des végétaux",
        "url": reverse_lazy("sv:evenement-liste"),
        "help_url": "https://doc-sv.seves.beta.gouv.fr",
    }
    ssa_domain = {
        "icon": "fr-icon-restaurant-line ",
        "nom": "Sécurité sanitaire des aliments",
        "url": reverse_lazy("ssa:evenement-produit-liste"),
        "help_url": "https://doc-ssa.seves.beta.gouv.fr",
    }

    current_domain = {}
    other_domains = []
    if hasattr(request, "domain"):
        if request.domain == "sv":
            current_domain = sv_domain
        elif request.domain == "ssa":
            current_domain = ssa_domain

        if settings.SV_GROUP in user_groups and not request.domain == "sv":
            other_domains.append(sv_domain)
        if settings.SSA_GROUP in user_groups and not request.domain == "ssa":
            other_domains.append(ssa_domain)

    return {"current_domain": current_domain, "other_domains": other_domains}
