from django.core.exceptions import ValidationError
import re


def validate_numero_detection(value):
    pattern = r"^\d{4}\.\d+\.\d+$"
    if not re.fullmatch(pattern, value):
        raise ValidationError("Le format doit être AAAA.X.Y avec AAAA sur 4 chiffres et X, Y numériques.")
