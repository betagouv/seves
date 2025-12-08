import contextlib

import waffle
from csp.constants import UNSAFE_INLINE
from csp.middleware import CSPMiddleware
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import resolve

from core.constants import Domains


class LoginAndGroupRequiredMiddleware:
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

        user = request.user
        if not (user and user.is_authenticated):
            return redirect_to_login(request.get_full_path())

        with contextlib.suppress(ValueError):
            domain = Domains(match.app_name)
            if domain == "tiac" and not waffle.flag_is_active(request, "tiac"):
                raise PermissionDenied()

        needed_group = Domains.group_for_value(match.app_name)
        if needed_group:
            request.domain = match.app_name
            if needed_group in [g.name for g in user.groups.all()]:
                response = self.get_response(request)
                response.set_cookie("preferred_domain", match.app_name)
                return response
            raise PermissionDenied()

        return self.get_response(request)


class HomeRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.path == "/":
            groups = [g.name for g in request.user.groups.all()]
            preferred_domain = request.COOKIES.get("preferred_domain")
            if preferred_domain == "ssa" and settings.SSA_GROUP in groups:
                return redirect("ssa:evenement-produit-liste")
            if preferred_domain == "sv" and settings.SV_GROUP in groups:
                return redirect("sv:evenement-liste")
            if settings.SSA_GROUP in groups:
                return redirect("ssa:evenement-produit-liste")
            if settings.SV_GROUP in groups:
                return redirect("sv:evenement-liste")
        return self.get_response(request)


class SevesCSPMiddleware(CSPMiddleware):
    def get_policy_parts(self, request, response, report_only=False):
        policy_parts = super().get_policy_parts(request, response, report_only)

        if settings.ADMIN_ENABLED and request.path_info.startswith(f"/{settings.ADMIN_URL}/post_office/email/"):
            policy_parts.update = {
                "style-src": UNSAFE_INLINE,
            }

        return policy_parts
