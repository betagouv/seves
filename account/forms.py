from django import forms
from django.contrib.auth import get_user_model
from django.forms import CheckboxSelectMultiple, Media
from dsfr.forms import DsfrBaseForm

from core.fields import DSFRCheckboxInput
from core.form_mixins import js_module
from core.forms import DSFRForm

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
        users = kwargs.pop("users")
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = users
        self.fields["user"].label_from_instance = lambda obj: obj.agent.agent_with_structure

    @property
    def media(self):
        return super().media + Media(
            js=(js_module("account/permissions_admins.js"),),
        )
