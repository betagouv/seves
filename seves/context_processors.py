from django.conf import settings


def select_empty_choice(request):
    return {"select_empty_choice": settings.SELECT_EMPTY_CHOICE}


def environment_class(request):
    match settings.ENVIRONMENT:
        case "recette":
            return {"environment_class": "environment-banner environment-recette"}
        case "dev":
            return {"environment_class": "environment-banner environment-dev"}
        case _:
            return {"environment_class": ""}
