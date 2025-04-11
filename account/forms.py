from django import forms
from django.contrib.auth import get_user_model

from core.fields import DSFRCheckboxInput
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
