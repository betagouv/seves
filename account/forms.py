from django import forms
from django.contrib.auth import get_user_model

from core.fields import DSFRToogle
from core.form_mixins import DSFRForm

User = get_user_model()


class UserPermissionForm(DSFRForm, forms.Form):
    def __init__(self, **kwargs):
        users = kwargs.pop("users")
        super().__init__(**kwargs)
        for user in users:
            self.fields[f"user_{user.pk}"] = forms.BooleanField(
                required=False,
                widget=DSFRToogle(attrs={"class": "fr-toggle__input", "label": str(user.agent), "id": user.pk}),
            )
