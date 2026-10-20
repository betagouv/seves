from functools import partial
from itertools import groupby
from operator import attrgetter

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
    AUTRE = (
        "autre",
        "Sélectionnez cette valeur si vous souhaitez échanger au sujet d’un événement lié à une maladie exotique, notamment zoonotique, qui ne figure pas dans la liste proposée.",
    )
    SAISIE_FACULTATIVE = (
        "saisie_facultative",
        "La saisie de cette maladie dans Sèves n'est pas obligatoire. Elle reste possible si votre DDPP souhaite assurer son suivi dans l'outil.",
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
    especes_concernees = models.ManyToManyField(
        "sa.Espece",
        blank=True,
        related_name="maladies_concernees",
        verbose_name="Espèces concernées",
    )

    intitule_typage_niveau_2 = models.CharField(max_length=255, blank=True, verbose_name="Intitulé (niveau 2)")
    intitule_typage_niveau_3 = models.CharField(max_length=255, blank=True, verbose_name="Intitulé (niveau 3)")
    intitule_typage_champ_libre = models.CharField(max_length=255, verbose_name="Intitulé champ libre")

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
            categorised_label=self.name_with_acronym,
            html_name_prefix=None,
        )

    def _treeselect_choice_with_typages(self):
        typages = [typage for typage in self.typages.all() if typage.valeur_niveau_2]
        if not typages:
            return self._treeselect_item

        niveaux_2 = []
        for valeur_niveau_2, typages_niveau_2 in groupby(typages, key=attrgetter("valeur_niveau_2")):
            typages_niveau_2 = list(typages_niveau_2)
            value = typages_niveau_2[0].niveau_2_value
            niveaux_3 = [
                TreeselectItem(value=typage.niveau_3_value, label=typage.valeur_niveau_3, categorised_label=None)
                for typage in typages_niveau_2
                if typage.valeur_niveau_3
            ]
            niveaux_2.append(
                TreeselectGroup(value=value, label=valeur_niveau_2, categorised_label=None, choices=niveaux_3)
                if niveaux_3
                else TreeselectItem(value=value, label=valeur_niveau_2, categorised_label=None)
            )

        return TreeselectGroup(
            value=self.pk, label=self.name_with_acronym, categorised_label=self.name_with_acronym, choices=niveaux_2
        )

    @staticmethod
    def _build_treeselect_choices(*, with_typages=False):
        queryset = Maladie.objects.order_by("name")
        if with_typages:
            queryset = queryset.prefetch_related("typages")

        def build_choices(maladies):
            return [
                maladie._treeselect_choice_with_typages() if with_typages else maladie._treeselect_item
                for maladie in maladies
            ]

        most_frequent_group = TreeselectGroup(
            label="Les plus fréquentes",
            choices=build_choices(queryset.filter(is_highlighted=True)),
            categorised_label=None,
            can_expand=False,
        )
        other_group = TreeselectGroup(
            label="Autre",
            choices=build_choices(queryset.filter(is_highlighted=False)),
            categorised_label=None,
        )

        return (most_frequent_group, other_group)

    @classproperty
    def treeselect_choices(cls):
        return lazy(cls._build_treeselect_choices, tuple)()

    @classproperty
    def treeselect_choices_with_typages(cls):
        return lazy(partial(cls._build_treeselect_choices, with_typages=True), tuple)()

    @staticmethod
    def choices_with_typages():
        choices = []
        for maladie in Maladie.objects.prefetch_related("typages"):
            choices.append((maladie.pk, maladie.name_with_acronym))
            for typage in maladie.typages.all():
                choices.append((typage.niveau_2_value, typage.valeur_niveau_2))
                choices.append((typage.niveau_3_value, typage.valeur_niveau_3))
        return choices

    @staticmethod
    def _build_all_treeselect_choices():
        return tuple(maladie._treeselect_item for maladie in Maladie.objects.order_by("name"))

    @classproperty
    def all_treeselect_choices(cls):
        return lazy(cls._build_all_treeselect_choices, tuple)()
