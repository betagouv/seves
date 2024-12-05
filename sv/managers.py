from django.db import models
from django.db.models import Q, Prefetch, OuterRef, Subquery, Count
from core.models import Visibilite


class LaboratoireAgreeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class LaboratoireConfirmationOfficielleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class StructurePreleveurManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class FicheDetectionManager(models.Manager):
    def get_queryset(self):
        return FicheDetectionQuerySet(self.model, using=self._db).filter(is_deleted=False)


class BaseVisibilityQuerySet(models.QuerySet):
    def get_fiches_user_can_view(self, user):
        """Renvoi les fiches que l'utilisateur peut voir en fonction de sa structure et de la visibilité de la fiche"""
        if user.agent.structure.is_mus_or_bsv:
            return self.filter(
                Q(visibilite__in=[Visibilite.LOCAL, Visibilite.NATIONAL])
                | Q(visibilite=Visibilite.BROUILLON, createur=user.agent.structure)
            )
        return self.filter(
            Q(visibilite=Visibilite.NATIONAL)
            | Q(
                visibilite__in=[Visibilite.BROUILLON, Visibilite.LOCAL],
                createur=user.agent.structure,
            )
        )

    def exclude_brouillon(self):
        return self.exclude(visibilite=Visibilite.BROUILLON)


class FicheDetectionQuerySet(BaseVisibilityQuerySet):
    def get_contacts_structures_not_in_fin_suivi(self, fiche_detection):
        contacts_structure_fiche = fiche_detection.contacts.exclude(structure__isnull=True).select_related("structure")
        fin_suivi_contacts_ids = fiche_detection.fin_suivi.values_list("contact", flat=True)
        contacts_not_in_fin_suivi = contacts_structure_fiche.exclude(id__in=fin_suivi_contacts_ids)
        return contacts_not_in_fin_suivi

    def with_list_of_lieux(self):
        from sv.models import Lieu

        lieux_prefetch = Prefetch("lieux", queryset=Lieu.objects.order_by("id"), to_attr="lieux_list")
        return self.prefetch_related(lieux_prefetch)

    def with_first_region_name(self):
        from sv.models import Lieu

        first_lieu = Lieu.objects.filter(fiche_detection=OuterRef("pk")).order_by("id")
        return self.annotate(region=Subquery(first_lieu.values("departement__region__nom")[:1]))

    def optimized_for_list(self):
        return self.select_related("etat", "numero", "organisme_nuisible", "createur")

    def order_by_numero_fiche(self):
        return self.order_by("-numero__annee", "-numero__numero")

    def optimized_for_details(self):
        return self.select_related(
            "statut_reglementaire", "etat", "numero", "contexte", "createur", "statut_evenement", "organisme_nuisible"
        )

    def get_all_not_in_fiche_zone_delimitee(self, organisme_nuisible_libelle, instance=None):
        query = Q(zone_infestee__isnull=True, hors_zone_infestee__isnull=True)
        if instance is not None:
            query |= Q(hors_zone_infestee=instance) | Q(zone_infestee__fiche_zone_delimitee=instance)
        return (
            self.filter(query)
            .filter(organisme_nuisible__libelle_court=organisme_nuisible_libelle)
            .select_related("numero")
        )

    def with_fiche_zone_delimitee_numero(self):
        return self.select_related("hors_zone_infestee__numero", "zone_infestee__fiche_zone_delimitee__numero")


class FicheZoneManager(models.Manager):
    def get_queryset(self):
        return FicheZoneQuerySet(self.model, using=self._db)


class FicheZoneQuerySet(BaseVisibilityQuerySet):
    def optimized_for_list(self):
        return self.select_related("numero", "createur", "organisme_nuisible", "etat")

    def order_by_numero_fiche(self):
        return self.order_by("-numero__annee", "-numero__numero")

    def get_contacts_structures_not_in_fin_suivi(self, fiche_zone_delimitee):
        contacts_structure_fiche = fiche_zone_delimitee.contacts.exclude(structure__isnull=True).select_related(
            "structure"
        )
        fin_suivi_contacts_ids = fiche_zone_delimitee.fin_suivi.values_list("contact", flat=True)
        contacts_not_in_fin_suivi = contacts_structure_fiche.exclude(id__in=fin_suivi_contacts_ids)
        return contacts_not_in_fin_suivi

    def with_nb_fiches_detection(self):
        return self.annotate(
            nb_fiches_detection=Count("fichedetection__id", distinct=True)
            + Count("zoneinfestee__fichedetection__id", distinct=True)
        )
