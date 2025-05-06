from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.views.generic import FormView

from account.forms import UserPermissionForm
from core.redirect import safe_redirect
from seves import settings

User = get_user_model()


class HandlePermissionsView(FormView):
    form_class = UserPermissionForm
    template_name = "user_permissions.html"

    def dispatch(self, request, *args, **kwargs):
        user_groups = request.user.groups.values_list("name", flat=True)
        if "access_admin" in user_groups:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied

    def get_users_in_structure(self):
        if hasattr(self, "users_in_structure"):
            return self.users_in_structure

        structure = self.request.user.agent.structure
        self.users_in_structure = (
            User.objects.exclude(pk=self.request.user.pk)
            .filter(agent__structure=structure)
            .select_related("agent")
            .order_by("agent__nom")
        )
        return self.users_in_structure

    def get_initial(self):
        initial = super().get_initial()
        user_to_is_active = {v.get("pk"): v.get("is_active") for v in User.objects.values("pk", "is_active")}
        for user in self.get_users_in_structure():
            initial[f"user_{user.pk}"] = user_to_is_active[user.pk]
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"users": self.get_users_in_structure()})
        return kwargs

    def form_valid(self, form):
        sv_group = Group.objects.get(name=settings.SV_GROUP)
        for key in form.changed_data:
            value = form.cleaned_data[key]
            if not (value in (True, False) and key.startswith("user_")):
                continue

            pk = key.replace("user_", "")
            user = User.objects.get(pk=pk)
            user.is_active = value
            user.save()
            user.groups.add(sv_group)
        messages.success(self.request, "Modification de droits enregistrées sur Sèves Santé des végétaux")
        return safe_redirect(self.request.POST.get("next"))
