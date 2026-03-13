from datetime import date, datetime

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import FieldDoesNotExist
from django.utils.html import strip_tags

from core.models import Departement


class BaseExport:
    blank_value = None

    def get_field_value(self, instance, field):
        attrs = field.split("__")
        for i, attr in enumerate(attrs):
            is_last = i == len(attrs) - 1

            if instance is None:
                return ""

            value = getattr(instance, attr)
            if value is None:
                return self.blank_value

            try:
                model_field = instance._meta.get_field(attr)
            except FieldDoesNotExist:
                model_field = None

            if is_last:
                display_method = f"get_{attr}_display"

                if hasattr(instance, display_method):
                    return getattr(instance, display_method)()
                if (
                    model_field
                    and isinstance(model_field, ArrayField)
                    and getattr(model_field.base_field, "choices", None)
                ):
                    choices_dict = dict(model_field.base_field.choices)
                    return ", ".join(strip_tags(choices_dict.get(v, v)) for v in value or [])
                if isinstance(value, list):
                    return ",".join(value) if value else None
                if isinstance(value, datetime):
                    return value.strftime("%d/%m/%Y %Hh%M")
                if isinstance(value, date):
                    return value.strftime("%d/%m/%Y")
                if isinstance(value, Departement):
                    return str(value)
                if isinstance(value, bool):
                    return "Oui" if value is True else "Non"
                return value

            instance = value

    def add_data(self, result, instance, fields):
        for field, header in fields:
            result[header] = self.get_field_value(instance, field)
        return result
