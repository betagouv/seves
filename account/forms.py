from django import forms
from django.contrib.auth import get_user_model
from django.forms import CheckboxSelectMultiple, Media
from dsfr.forms import DsfrBaseForm

from core.fields import DSFRCheckboxInput
from core.form_mixins import js_module
from core.forms import DSFRForm
from seves.settings import CAN_GIVE_ACCESS_GROUP, SSA_GROUP, SV_GROUP

User = get_user_model()


class UserPermissionForm(DSFRForm, forms.Form):
    def __init__(self, **kwargs):
        users = kwargs.pop("users")
        can_manage_sv = kwargs.pop("can_manage_sv", False)
        can_manage_ssa = kwargs.pop("can_manage_ssa", False)
        super().__init__(**kwargs)
        for user in users:
            if can_manage_sv:
                self.fields[f"sv_{user.pk}"] = forms.BooleanField(
                    required=False,
                    widget=DSFRCheckboxInput(
                        attrs={"id": f"sv_{user.pk}"},
                        label="",
                    ),
                )
            if can_manage_ssa:
                self.fields[f"ssa_{user.pk}"] = forms.BooleanField(
                    required=False,
                    widget=DSFRCheckboxInput(
                        attrs={"id": f"ssa_{user.pk}"},
                        label="",
                    ),
                )


class AddAdminForm(DsfrBaseForm, forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.none(), label="Agent")
    domains = forms.MultipleChoiceField(choices=[("SV", "SV"), ("SSA", "SSA")], widget=CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        groups = [CAN_GIVE_ACCESS_GROUP, SV_GROUP, SSA_GROUP]
        existing_admin_with_all_groups = User.objects

        for g in groups:
            existing_admin_with_all_groups = existing_admin_with_all_groups.filter(groups__name=g)

        existing_admin_with_all_groups = existing_admin_with_all_groups.values_list("pk", flat=True)
        self.fields["user"].queryset = User.objects.exclude(pk__in=existing_admin_with_all_groups).select_related(
            "agent", "agent__structure"
        )
        self.fields["user"].label_from_instance = lambda obj: obj.agent.agent_with_structure

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("account/permissions_admins.js"),),
        )
