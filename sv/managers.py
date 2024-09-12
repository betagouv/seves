from django.db import models


class FicheDetectionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def get_contacts_structures_not_in_fin_suivi(self, fiche_detection):
        contacts_structure_fiche = fiche_detection.contacts.exclude(structure__isnull=True).select_related("structure")
        fin_suivi_contacts_ids = fiche_detection.fin_suivi.values_list("contact", flat=True)
        contacts_not_in_fin_suivi = contacts_structure_fiche.exclude(id__in=fin_suivi_contacts_ids)
        return contacts_not_in_fin_suivi
