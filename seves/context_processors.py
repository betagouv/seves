from django.conf import settings


def select_empty_choice(request):
    return {"select_empty_choice": settings.SELECT_EMPTY_CHOICE}


def environment_class(request):
    return {"environment_class": "environment-recette" if settings.ENVIRONMENT == "recette" else ""}
