from enum import auto

from django.db.models import IntegerChoices


class EvenementOrigin(IntegerChoices):
    ARS = auto(), "ARS"
    CONSUMER = auto(), "Consommateur"
    ETABLISSEMENT = auto(), "Établissement"
    DOCTOR = auto(), "Médecin"
    OTHER = auto(), "Autre"


class ModaliteDeclarationEvenement(IntegerChoices):
    SIGNAL_CONSO = auto(), "SignalConso"
    OTHER = auto(), "Autre"


class EvenementFollowUp(IntegerChoices):
    NONE = auto(), "Aucune suite"
    INSPECTION = auto(), "Programmation d’un futur contrôle"
