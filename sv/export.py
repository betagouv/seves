from .models import FicheDetection
import csv


class FicheDetectionExport:
    fields = [
        "numero",
        "numero_europhyt",
        "numero_rasff",
        "statut_evenement",
        "organisme_nuisible",
        "statut_reglementaire",
        "date_premier_signalement",
        "commentaire",
        "mesures_conservatoires_immediates",
        "mesures_consignation",
        "mesures_phytosanitaires",
        "mesures_surveillance_specifique",
        "etat",
        "date_creation",
    ]
    lieux_fields = [
        "nom",
        "wgs84_longitude",
        "wgs84_latitude",
        "lambert93_latitude",
        "lambert93_longitude",
        "adresse_lieu_dit",
        "commune",
        "code_insee",
        "departement",
    ]
    prelevement_fields = [
        "numero_echantillon",
        "date_prelevement",
        "is_officiel",
        "numero_phytopass",
        "resultat",
        "structure_preleveur",
        "site_inspection",
        "matrice_prelevee",
        "espece_echantillon",
        "laboratoire_agree",
        "laboratoire_confirmation_officielle",
    ]

    def _clean_field_name(self, field):
        return field.replace("_", " ").title()

    def get_queryset(self):
        queryset = FicheDetection.objects.select_related("etat", "numero")
        queryset = queryset.prefetch_related("lieux", "lieux__prelevements", "lieux__prelevements__structure_preleveur")
        return queryset

    def get_fieldnames(self):
        return [self._clean_field_name(field) for field in self.fields + self.lieux_fields + self.prelevement_fields]

    def get_fiche_data(self, fiche):
        result = {}
        for field in self.fields:
            result[self._clean_field_name(field)] = getattr(fiche, field)
        return result

    def get_fiche_data_with_lieu(self, fiche, lieu):
        result = self.get_fiche_data(fiche)
        for field in self.lieux_fields:
            result[self._clean_field_name(field)] = getattr(lieu, field)
        return result

    def get_fiche_data_with_prelevement(self, fiche, prelevement):
        result = self.get_fiche_data_with_lieu(fiche, prelevement.lieu)
        for field in self.prelevement_fields:
            result[self._clean_field_name(field)] = getattr(prelevement, field)
        return result

    def get_lines_from_instance(self, fiche_detection):
        lieux = fiche_detection.lieux.all()
        if lieux:
            for lieu in lieux:
                prelevements = lieu.prelevements.all()
                if prelevements:
                    for prelevement in prelevements:
                        yield self.get_fiche_data_with_prelevement(fiche_detection, prelevement)
                else:
                    yield self.get_fiche_data_with_lieu(fiche_detection, lieu)
        else:
            yield self.get_fiche_data(fiche_detection)

    def export(self, stream):
        queryset = self.get_queryset()
        writer = csv.DictWriter(stream, fieldnames=self.get_fieldnames())
        writer.writeheader()

        for instance in queryset:
            for line in self.get_lines_from_instance(instance):
                writer.writerow(line)
