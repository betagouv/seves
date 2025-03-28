import re

from django.core.exceptions import ValidationError


def validate_numero_rasff(value):
    if not re.match(r"^\d{4}\.\d{4}$", value) and not re.match(r"^AA\d{2}\.\d{4}$", value):
        raise ValidationError("Format invalide. Utilisez 'XXXX.YYYY' (2025.1234) ou 'AAXX.YYYY' (AA25.1234)")
