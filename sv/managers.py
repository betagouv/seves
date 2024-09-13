from django.db import models
from django.db.models import Q
from core.models import Visibilite


class FicheDetectionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def get_contacts_structures_not_in_fin_suivi(self, fiche_detection):
        contacts_structure_fiche = fiche_detection.contacts.exclude(structure__isnull=True).select_related("structure")
        fin_suivi_contacts_ids = fiche_detection.fin_suivi.values_list("contact", flat=True)
        contacts_not_in_fin_suivi = contacts_structure_fiche.exclude(id__in=fin_suivi_contacts_ids)
        return contacts_not_in_fin_suivi

    def get_fiches_user_can_view(self, user):
        """Renvoi les fiches (queryset) que l'utilisateur peut voir en fonction de sa structure et de la visibilité de la fiche"""
        if user.agent.structure.is_mus_or_bsv:
            return self.get_queryset().filter(
                Q(visibilite__in=[Visibilite.LOCAL, Visibilite.NATIONAL])
                | Q(visibilite=Visibilite.BROUILLON, createur=user.agent.structure)
            )
        return self.get_queryset().filter(
            Q(visibilite=Visibilite.NATIONAL)
            | Q(
                visibilite__in=[Visibilite.BROUILLON, Visibilite.LOCAL],
                createur=user.agent.structure,
            )
        )
