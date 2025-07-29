from django.db.models import TextChoices


class EvenementOrigin(TextChoices):
    ARS = "ars", "ARS"
    CONSUMER = "consommateur", "Consommateur"
    ETABLISSEMENT = "etablissement", "Établissement"
    DOCTOR = "medecin", "Médecin"
    OTHER = "autre", "Autre"


class ModaliteDeclarationEvenement(TextChoices):
    SIGNAL_CONSO = "signalconso", "SignalConso"
    OTHER = "autre", "Autre"


class EvenementFollowUp(TextChoices):
    NONE = "aucune suite", "Aucune suite"
    INSPECTION = "programmation futur controle", "Programmation d’un futur contrôle"
