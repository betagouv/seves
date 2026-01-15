from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from account.forms import UserPermissionForm, AddAdminForm
from account.notifications import notify_new_permission, notify_remove_permission, notify_new_admin_permission
from core.models import Contact
from core.redirect import safe_redirect
from core.mixins import MediaDefiningMixin
from seves import settings
from seves.settings import CAN_GIVE_ACCESS_GROUP

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
        user_changes = defaultdict(lambda: {"added": [], "removed": []})

        for key in form.changed_data:
            value = form.cleaned_data[key]
            if not (value in (True, False) and (key.startswith("sv_") or key.startswith("ssa_"))):
                continue
            group_name, user_pk = key.upper().split("_")
            user = self.get_users_in_structure().get(pk=user_pk)
            group_mapping = {"SV": (self.sv_group, self.can_manage_sv), "SSA": (self.ssa_group, self.can_manage_ssa)}
            target_group, can_manage = group_mapping.get(group_name)
            if can_manage:
                if value:
                    user.groups.add(target_group)
                    user_changes[user_pk]["added"].append(group_name)
                else:
                    user.groups.remove(target_group)
                    user_changes[user_pk]["removed"].append(group_name)

        for user_pk, changes in user_changes.items():
            contact_agent = Contact.objects.get(agent__user__pk=user_pk)
            user = contact_agent.agent.user
            is_in_sv = user.groups.filter(name=settings.SV_GROUP).exists()
            is_in_ssa = user.groups.filter(name=settings.SSA_GROUP).exists()
            should_be_active = is_in_sv or is_in_ssa
            if user.is_active != should_be_active:
                user.is_active = should_be_active
                user.save()
            if changes["added"]:
                notify_new_permission(contact_agent, changes["added"])
            if changes["removed"]:
                notify_remove_permission(contact_agent, changes["removed"])
        messages.success(self.request, "Modification de droits enregistrées")
        return safe_redirect(self.request.POST.get("next"))


class HandleAdminsView(UserPassesTestMixin, MediaDefiningMixin, FormView):
    template_name = "user_admins.html"
    form_class = AddAdminForm
    success_url = reverse_lazy("handle-admins")

    def test_func(self):
        return self.request.user.agent.structure.is_mus

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["existing_admins"] = (
            Group.objects.get(name=CAN_GIVE_ACCESS_GROUP)
            .user_set.all()
            .prefetch_related("groups")
            .select_related("agent", "agent__structure")
        )
        for admin in context["existing_admins"]:
            admin.domains = ", ".join(
                [
                    g.name.split("_user")[0].title()
                    for g in admin.groups.filter(name__in=[settings.SV_GROUP, settings.SSA_GROUP])
                ]
            )
        return context

    def get_media(self, **context_data):
        return context_data["form"].media

    def post(self, request, *args, **kwargs):
        if request.POST.get("action") == "remove":
            admin_group = Group.objects.get(name=CAN_GIVE_ACCESS_GROUP)
            user = User.objects.get(pk=request.POST.get("user"))
            user.groups.remove(admin_group)
            messages.success(self.request, "Le rôle administrateur a été révoqué")
            return HttpResponseRedirect(self.get_success_url())

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)

        user = form.cleaned_data["user"]
        user.is_active = True
        user.groups.add(Group.objects.get(name=CAN_GIVE_ACCESS_GROUP))
        user.save()
        if "SV" in form.cleaned_data["domains"]:
            user.groups.add(Group.objects.get(name=settings.SV_GROUP))
        if "SSA" in form.cleaned_data["domains"]:
            user.groups.add(Group.objects.get(name=settings.SSA_GROUP))

        notify_new_admin_permission(user.agent.contact_set.get(), form.cleaned_data["domains"])
        messages.success(self.request, "Le rôle administrateur a été accordé")
        return response

    def form_invalid(self, form):
        response = super().form_valid(form)
        messages.error(self.request, "Erreur de traitement")
        return response
