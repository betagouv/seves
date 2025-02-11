from django.db import models
from django.db.models import Q, Prefetch, OuterRef, Subquery, Count

from core.models import Visibilite


class LaboratoireManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class StructurePreleveuseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class FicheDetectionManager(models.Manager):
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


class BaseVisibilityQuerySet(models.QuerySet):
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


class FicheDetectionQuerySet(BaseVisibilityQuerySet):
    def with_list_of_lieux_with_commune(self):
        from sv.models import Lieu

        lieux_prefetch = Prefetch(
            "lieux", queryset=Lieu.objects.exclude(commune="").order_by("id"), to_attr="lieux_list_with_commune"
        )
        return self.prefetch_related(lieux_prefetch)

    def with_first_region_name(self):
        from sv.models import Lieu

        first_lieu = Lieu.objects.filter(fiche_detection=OuterRef("pk")).order_by("id")
        return self.annotate(region=Subquery(first_lieu.values("departement__region__nom")[:1]))

    def optimized_for_list(self):
        return self.select_related("createur", "evenement", "evenement__organisme_nuisible")

    def order_by_numero_fiche(self):
        return self.order_by("-numero_detection")

    def optimized_for_details(self):
        return self.select_related("contexte", "createur", "evenement", "statut_evenement")

    def get_all_not_in_fiche_zone_delimitee(self, instance):
        query = Q(zone_infestee__isnull=True, hors_zone_infestee__isnull=True)
        query |= Q(hors_zone_infestee=instance) | Q(zone_infestee__fiche_zone_delimitee=instance)
        return self.filter(query)

    def with_fiche_zone_delimitee_numero(self):
        return self.select_related("hors_zone_infestee__numero", "zone_infestee__fiche_zone_delimitee__numero")


class FicheZoneManager(models.Manager):
    def get_queryset(self):
        return FicheZoneQuerySet(self.model, using=self._db)


class FicheZoneQuerySet(BaseVisibilityQuerySet):
    def optimized_for_list(self):
        return self.select_related("createur", "evenement", "evenement__organisme_nuisible")

    def order_by_numero_fiche(self):
        return self.order_by("-evenement__numero_annee", "-evenement__numero_evenement")

    def with_nb_fiches_detection(self):
        return self.annotate(
            nb_fiches_detection=Count("fichedetection__id", distinct=True)
            + Count("zoneinfestee__fichedetection__id", distinct=True)
        )


class EvenementManager(models.Manager):
    def get_queryset(self):
        return EvenementQueryset(self.model, using=self._db).filter(is_deleted=False)


class EvenementQueryset(models.QuerySet):
    def order_by_numero(self):
        return self.order_by("-numero_annee", "-numero_evenement")

    def get_user_can_view(self, user):
        from sv.models import Evenement

        if user.agent.structure.is_mus_or_bsv:
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
