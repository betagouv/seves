from django.conf import settings


def select_empty_choice(request):
    return {"select_empty_choice": settings.SELECT_EMPTY_CHOICE}
