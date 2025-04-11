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
        sv_group = Group.objects.get(name=settings.SV_GROUP)
        ssa_group = Group.objects.get(name=settings.SSA_GROUP)
        sv_users = User.objects.filter(groups=sv_group).values_list("pk", flat=True)
        ssa_users = User.objects.filter(groups=ssa_group).values_list("pk", flat=True)
        for user in self.get_users_in_structure():
            initial[f"sv_{user.pk}"] = user.pk in sv_users
            initial[f"ssa_{user.pk}"] = user.pk in ssa_users
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"users": self.get_users_in_structure()})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users_with_fields = []
        for user_obj in self.get_users_in_structure():
            user_data = {
                "user": user_obj,
                "sv_field": self.get_form()[f"sv_{user_obj.pk}"],
                "ssa_field": self.get_form()[f"ssa_{user_obj.pk}"],
            }
            users_with_fields.append(user_data)
        context["users_with_fields"] = users_with_fields
        return context

    def form_valid(self, form):
        sv_group = Group.objects.get(name=settings.SV_GROUP)
        ssa_group = Group.objects.get(name=settings.SSA_GROUP)
        for user in self.get_users_in_structure():
            is_in_sv = form.cleaned_data.get(f"sv_{user.pk}", False)
            is_in_ssa = form.cleaned_data.get(f"ssa_{user.pk}", False)
            user.groups.add(sv_group) if is_in_sv else user.groups.remove(sv_group)
            user.groups.add(ssa_group) if is_in_ssa else user.groups.remove(ssa_group)
            should_be_active = is_in_sv or is_in_ssa
            if user.is_active != should_be_active:
                user.is_active = should_be_active
                user.save()
        messages.success(self.request, "Modification de droits enregistrées sur Sèves Santé des végétaux")
        return safe_redirect(self.request.POST.get("next"))
