from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from django.conf import settings
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class LoginView(TemplateView):
    template_name = "core/login.html"


def logout(request):
    return settings.OIDC_RP_LOGOUT_ENDPOINT


class CustomOIDCAuthenticationCallbackView(OIDCAuthenticationCallbackView):
    def login_failure(self):
        logger.info("In login failure")
        if self.user and not self.user.is_active:
            logger.info(f"In login failure {self.user}")
            logger.info(f"In login failure {self.user.is_active}")
            if hasattr(self.user, "agent") and hasattr(self.user.agent, "structure"):
                users_in_structure = User.objects.filter(agent__structure=self.user.agent.structure, is_active=True)
                users_in_structure = users_in_structure.select_related("agent__structure")
                group_name = settings.CAN_GIVE_ACCESS_GROUP
                admin_users = [u for u in users_in_structure if group_name in u.groups.values_list("name", flat=True)]
                return render(self.request, "login_denied.html", {"admin_users": admin_users})
        return HttpResponseRedirect(self.failure_url)
