from django.views.generic import TemplateView
from django.conf import settings


class LoginView(TemplateView):
    template_name = "core/login.html"


def logout(request):
    return settings.OIDC_RP_LOGOUT_ENDPOINT
