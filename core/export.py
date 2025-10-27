from datetime import datetime

from core.models import Departement


class BaseExport:
    def get_field_value(self, instance, field):
        attrs = field.split("__")
        for i, attr in enumerate(attrs):
            is_last_level_attribute = len(attrs) - 1
            if i == is_last_level_attribute:
                display_method = f"get_{attr}_display"
                if hasattr(instance, display_method):
                    return getattr(instance, display_method)()
            value = getattr(instance, attr, None)
            if value is None:
                return ""
            if isinstance(value, list):
                return ",".join(value) if value else None
            if isinstance(value, datetime):
                return value.strftime("%d/%m/%Y %Hh%M")
            if isinstance(value, Departement):
                return str(value)
            if isinstance(value, bool):
                return "Oui" if value is True else "Non"
            return value

    def add_data(self, result, instance, fields):
        for field, header in fields:
            result[header] = self.get_field_value(instance, field)
        return result
