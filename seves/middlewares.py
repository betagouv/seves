from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import resolve


class LoginRequiredMiddleware:
    authorized_routes = [
        "login",
        "oidc_authentication_callback",
        "oidc_authentication_init",
        "custom_oidc_authentication_callback",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        match = resolve(request.path_info)
        if match and match.url_name in self.authorized_routes:
            return self.get_response(request)

        if not request.user:
            return HttpResponseRedirect(settings.LOGIN_URL)
        if not request.user.is_authenticated:
            return HttpResponseRedirect(settings.LOGIN_URL)

        return self.get_response(request)
