from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q, Prefetch, OuterRef, Subquery, Count, Exists
from django.db.models.functions import Cast, Greatest
from core.models import Visibilite, FinSuiviContact, user_is_referent_national

from django.db.models import IntegerField, Func, Value

from sv.managers_mixins import WithDerniereMiseAJourManagerMixin


class SplitPart(Func):
    function = "SPLIT_PART"
    arity = 3


class LaboratoireManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class StructurePreleveuseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class FicheDetectionManager(WithDerniereMiseAJourManagerMixin, models.Manager):
    def get_queryset(self):
        return FicheDetectionQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def get_last_used_numero(self, evenement_id):
        from sv.models import FicheDetection

        fiches = (
            FicheDetection._base_manager.select_for_update()
            .filter(evenement_id=evenement_id)
            .values_list("numero_detection", flat=True)
        )
        if fiches:
            last_parts = [int(v.split(".")[-1]) for v in fiches]
            return max(last_parts)
        return 0


class FichesCommonQueryset(models.QuerySet):
    def get_fiches_user_can_view(self, user):
        from sv.models import Evenement

        if user.agent.structure.is_mus_or_bsv:
            return self.exclude(Q(evenement__etat=Evenement.Etat.BROUILLON) & ~Q(createur=user.agent.structure))
        return self.filter(
            Q(evenement__visibilite=Visibilite.NATIONALE)
            | Q(createur=user.agent.structure)
            | Q(
                ~Q(evenement__etat=Evenement.Etat.BROUILLON)
                & Q(evenement__visibilite=Visibilite.LIMITEE)
                & Q(evenement__allowed_structures=user.agent.structure)
            )
        )


class FicheDetectionQuerySet(FichesCommonQueryset):
    def with_first_region_name(self):
        from sv.models import Lieu

        first_lieu = Lieu.objects.filter(fiche_detection=OuterRef("pk")).order_by("id")
        return self.annotate(region=Subquery(first_lieu.values("departement__region__nom")[:1]))

    def with_numero_detection_only(self):
        return self.annotate(
            numero_detection_only=Cast(SplitPart("numero_detection", Value("."), 3), IntegerField()),
        )

    def order_by_numero_fiche(self):
        return self.with_numero_detection_only().order_by(
            "-evenement__numero_annee", "-evenement__numero_evenement", "-numero_detection_only"
        )

    def optimized_for_details(self):
        return self.select_related("contexte", "createur", "evenement", "statut_evenement")

    def get_all_not_in_fiche_zone_delimitee(self, instance):
        query = Q(zone_infestee__isnull=True, hors_zone_infestee__isnull=True)
        query |= Q(hors_zone_infestee=instance) | Q(zone_infestee__fiche_zone_delimitee=instance)
        return self.filter(query)


class FicheZoneManager(WithDerniereMiseAJourManagerMixin, models.Manager):
    def get_queryset(self):
        return FicheZoneQuerySet(self.model, using=self._db)


class FicheZoneQuerySet(FichesCommonQueryset):
    def order_by_numero_fiche(self):
        return self.order_by("-evenement__numero_annee", "-evenement__numero_evenement")

    def with_nb_fiches_detection(self):
        return self.annotate(
            nb_fiches_detection=Count("fichedetection__id", distinct=True)
            + Count("zoneinfestee__fichedetection__id", distinct=True)
        )


class EvenementManager(WithDerniereMiseAJourManagerMixin, models.Manager):
    def get_queryset(self):
        return EvenementQueryset(self.model, using=self._db).filter(is_deleted=False)


class EvenementQueryset(models.QuerySet):
    def order_by_numero(self):
        return self.order_by("-numero_annee", "-numero_evenement")

    def with_date_derniere_mise_a_jour(self):
        """
        Calcule la date la plus récente de modification parmi l'événement,
        ses détections et sa fiche zone délimitée, puis trie le queryset par cette date.
        """
        return self.annotate(
            date_derniere_mise_a_jour_detections=models.Max(
                "detections__date_derniere_mise_a_jour",
            ),
            date_derniere_mise_a_jour_zone=models.F(
                "fiche_zone_delimitee__date_derniere_mise_a_jour",
            ),
            date_derniere_mise_a_jour_globale=Greatest(
                "date_derniere_mise_a_jour",
                "date_derniere_mise_a_jour_detections",
                "date_derniere_mise_a_jour_zone",
                output_field=models.DateTimeField(),
            ),
        )

    def get_user_can_view(self, user):
        from sv.models import Evenement

        if user.agent.structure.is_mus_or_bsv or user_is_referent_national(user):
            return self.exclude(Q(etat=Evenement.Etat.BROUILLON) & ~Q(createur=user.agent.structure))
        return self.filter(
            Q(visibilite=Visibilite.NATIONALE)
            | Q(createur=user.agent.structure)
            | Q(
                ~Q(etat=Evenement.Etat.BROUILLON)
                & Q(visibilite=Visibilite.LIMITEE)
                & Q(allowed_structures=user.agent.structure)
            )
        )

    def with_list_of_lieux_with_commune(self):
        from sv.models import Lieu, FicheDetection

        lieux_prefetch = Prefetch(
            "lieux", queryset=Lieu.objects.exclude(commune="").order_by("id"), to_attr="lieux_list_with_commune"
        )
        detections_prefetch = Prefetch(
            "detections", queryset=FicheDetection.objects.filter(is_deleted=False).prefetch_related(lieux_prefetch)
        )
        return self.prefetch_related(detections_prefetch)

    def with_fin_de_suivi(self, contact):
        from sv.models import Evenement

        content_type = ContentType.objects.get_for_model(Evenement)
        return self.annotate(
            has_fin_de_suivi=Exists(
                FinSuiviContact.objects.filter(content_type=content_type, object_id=OuterRef("pk"), contact=contact)
            )
        )

    def with_nb_fiches_detection(self):
        return self.annotate(
            nb_fiches_detection=Count("detections", filter=Q(detections__is_deleted=False), distinct=True)
        )

    def optimized_for_list(self):
        return self.select_related("organisme_nuisible", "statut_reglementaire", "createur", "fiche_zone_delimitee")
