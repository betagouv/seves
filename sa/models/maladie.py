from django.db import models


class DescriptionType(models.TextChoices):
    NOTIFY_ASAP = (
        "notify_asap",
        "Cette maladie doit être notifiée dans Sèves dès le stade de la suspicion.",
    )
    NOTIFY_CONFIRMED = (
        "notify_confirmed",
        "Cette maladie doit être notifiée dans Sèves après confirmation. L’événement peut toutefois être créé dès le stade de la suspicion à des fins de suivi.",
    )
    NEW = (
        "new",
        "Suspicion de maladie émergente. Le cas index doit être notifié dans Sèves dès le stade de la suspicion, avant le déploiement de CartoGIP.",
    )
    CARTOGIP = (
        "cartogip",
        "Cette maladie doit être notifiée dans CartoGIP. Une interconnexion est prévue à terme avec Sèves.",
    )
    SALMONELLE = (
        "salmonelle",
        "La notification de cette maladie ne fait pas encore partie du périmètre de Sèves. Elle sera intégrée prochainement.",
    )
    TUBERCULOSE = (
        "tuberculose",
        "Les événements concernant une tuberculose peu commune ou dont on suspecte un impact zoonotique doivent être notifiés dans Sèves. Tous les autres événements restent traités dans SIGAL et CartoGIP.",
    )


class Maladie(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom", unique=True)
    acronym = models.CharField(max_length=5, verbose_name="Acronyme")
    description_type = models.CharField(
        max_length=512,
        choices=DescriptionType.choices,
        verbose_name="Type de description de l'action pour la maladie",
        null=False,
    )
    decert_id = models.CharField(max_length=255, verbose_name="Identifiant DECERT", blank=True)
    needs_arrete = models.BooleanField(default=False, verbose_name="Nécessite un APMS ou APDI")
    needs_date_nd = models.BooleanField(default=True, verbose_name="Nécessite une date ND")
    needs_dates_desinfection = models.BooleanField(default=False, verbose_name="Nécessite des dates D0, ND1, ND2")

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~(models.Q(needs_date_nd=True) & models.Q(needs_dates_desinfection=True)),
                name="maladie_needs_date_nd_and_needs_dates_desinfection_not_both_true",
            ),
        ]
