from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.middleware.csp import ContentSecurityPolicyMiddleware
from django.shortcuts import redirect
from django.urls import resolve
from django.utils.csp import CSP

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


class SevesCSPMiddleware(ContentSecurityPolicyMiddleware):
    def process_response(self, request, response):
        if settings.ADMIN_ENABLED and request.path_info.startswith(f"/{settings.ADMIN_URL}/post_office/email/"):
            csp_config = dict(getattr(response, "_csp_config", settings.SECURE_CSP) or {})
            csp_config.setdefault("style-src", [])
            csp_config["style-src"] = (*csp_config["style-src"], CSP.UNSAFE_INLINE)
            response._csp_config = csp_config

        return super().process_response(request, response)
