from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.urls import resolve


class LoginAndGroupRequiredMiddleware:
    authorized_routes = [
        "login",
        "oidc_authentication_callback",
        "oidc_authentication_init",
        "custom_oidc_authentication_callback",
    ]

    apps_to_groups = {
        "sv": settings.SV_GROUP,
        "ssa": settings.SSA_GROUP,
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        match = resolve(request.path_info)
        if match and match.url_name in self.authorized_routes:
            return self.get_response(request)

        user = request.user
        if not (user and user.is_authenticated):
            return redirect_to_login(request.get_full_path())

        needed_group = self.apps_to_groups.get(match.app_name)
        if needed_group:
            request.domain = match.app_name
            if needed_group in user.groups.values_list("name", flat=True):
                return self.get_response(request)
            raise PermissionDenied()

        return self.get_response(request)
