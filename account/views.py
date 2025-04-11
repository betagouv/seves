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
        self.user_groups = request.user.groups.values_list("name", flat=True)
        can_give_access = settings.CAN_GIVE_ACCESS_GROUP in self.user_groups
        self.can_manage_sv = settings.SV_GROUP in self.user_groups
        self.can_manage_ssa = settings.SSA_GROUP in self.user_groups
        if can_give_access and (self.can_manage_sv or self.can_manage_ssa):
            self.sv_group = Group.objects.get(name=settings.SV_GROUP)
            self.ssa_group = Group.objects.get(name=settings.SSA_GROUP)
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
            .prefetch_related("groups")
            .order_by("agent__nom")
        )
        return self.users_in_structure

    def get_initial(self):
        initial = super().get_initial()
        for user in self.get_users_in_structure():
            user_groups = user.groups.all()
            initial[f"sv_{user.pk}"] = self.sv_group in user_groups
            initial[f"ssa_{user.pk}"] = self.ssa_group in user_groups
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "users": self.get_users_in_structure(),
                "can_manage_sv": self.can_manage_sv,
                "can_manage_ssa": self.can_manage_ssa,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users_with_fields = []
        form = self.get_form()
        for user_obj in self.get_users_in_structure():
            user_data = {
                "user": user_obj,
            }
            if self.can_manage_sv:
                user_data["sv_field"] = form[f"sv_{user_obj.pk}"]
            if self.can_manage_ssa:
                user_data["ssa_field"] = form[f"ssa_{user_obj.pk}"]
            users_with_fields.append(user_data)
        context["users_with_fields"] = users_with_fields
        context["can_manage_sv"] = self.can_manage_sv
        context["can_manage_ssa"] = self.can_manage_ssa
        return context

    def form_valid(self, form):
        for user in self.get_users_in_structure():
            is_in_sv = user.groups.filter(name=settings.SV_GROUP).exists()
            is_in_ssa = user.groups.filter(name=settings.SSA_GROUP).exists()
            if self.can_manage_sv:
                is_in_sv = form.cleaned_data.get(f"sv_{user.pk}", False)
                user.groups.add(self.sv_group) if is_in_sv else user.groups.remove(self.sv_group)
            if self.can_manage_ssa:
                is_in_ssa = form.cleaned_data.get(f"ssa_{user.pk}", False)
                user.groups.add(self.ssa_group) if is_in_ssa else user.groups.remove(self.ssa_group)
            should_be_active = is_in_sv or is_in_ssa
            if user.is_active != should_be_active:
                user.is_active = should_be_active
                user.save()
        messages.success(self.request, "Modification de droits enregistrées")
        return safe_redirect(self.request.POST.get("next"))
