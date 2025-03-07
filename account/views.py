from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic import FormView

from account.forms import UserPermissionForm

User = get_user_model()


class HandlePermissionsView(SuccessMessageMixin, FormView):
    form_class = UserPermissionForm
    template_name = "user_permissions.html"
    success_url = reverse_lazy("handle-permissions")
    success_message = "Modification de droits enregistrées sur Sèves Santé des végétaux"

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
        for key in form.changed_data:
            value = form.cleaned_data[key]
            if not (value in (True, False) and key.startswith("user_")):
                continue

            pk = key.replace("user_", "")
            user = User.objects.get(pk=pk)
            user.is_active = value
            user.save()
        return super().form_valid(form)
