import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_numero_rasff(value):
    if not re.match(r"^\d{4}\.\d{4}$", value) and not re.match(r"^AA\d{2}\.\d{4}$", value):
        raise ValidationError("Format invalide. Utilisez 'XXXX.YYYY' (2025.1234) ou 'AAXX.YYYY' (AA25.1234)")


rappel_conso_validator = RegexValidator(regex=r"^\d{4}-\d{2}-\d{4}$", message="Le format doit être AAAA-XX-YYYY")


def validate_numero_agrement(value):
    pattern = r"^\d{2,3}\.\d{2,3}\.\d{2,3}$"
    if not re.match(pattern, value):
        raise ValidationError(f"{value} n'est pas un format valide.")
