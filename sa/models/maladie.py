from django.db import models
from django.utils.functional import classproperty, lazy

from core.widgets import TreeselectGroup, TreeselectItem


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
    is_highlighted = models.BooleanField(default=False, verbose_name="Est ce que c'est une maladie fréquente")

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~(models.Q(needs_date_nd=True) & models.Q(needs_dates_desinfection=True)),
                name="maladie_needs_date_nd_and_needs_dates_desinfection_not_both_true",
            ),
        ]

    @property
    def name_with_acronym(self):
        return self.name if self.acronym == "DIV" else f"{self.name} ({self.acronym})"

    @property
    def _treeselect_item(self):
        return TreeselectItem(
            value=self.pk,
            label=self.name_with_acronym,
            categorised_label=self.name,
            html_name_prefix=None,
        )

    @staticmethod
    def _build_treeselect_choices():
        most_frequent_queryset = Maladie.objects.filter(is_highlighted=True).order_by("name")
        most_frequent_choices = [maladie._treeselect_item for maladie in most_frequent_queryset]
        most_frequent_group = TreeselectGroup(
            label="Les plus fréquentes",
            choices=most_frequent_choices,
            categorised_label=None,
        )
        other_queryset = Maladie.objects.filter(is_highlighted=False).order_by("name")
        other_choices = [maladie._treeselect_item for maladie in other_queryset]
        other_group = TreeselectGroup(
            label="Autre",
            choices=other_choices,
            categorised_label=None,
        )

        return (most_frequent_group, other_group)

    @classproperty
    def treeselect_choices(cls):
        return lazy(cls._build_treeselect_choices, tuple)()
