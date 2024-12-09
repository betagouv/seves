from .models import FicheDetection, Prelevement, Lieu, StructurePreleveuse
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
        "adresse_lieu_dit",
        "commune",
        "code_insee",
        "departement",
    ]
    prelevement_fields = [
        "numero_echantillon",
        "date_prelevement",
        "is_officiel",
        "resultat",
        "structure_preleveuse",
        "matrice_prelevee",
        "espece_echantillon",
        "laboratoire_agree",
        "laboratoire_confirmation_officielle",
    ]

    def _clean_field_name(self, field, instance):
        return instance._meta.get_field(field).verbose_name

    def get_queryset(self, user):
        queryset = FicheDetection.objects.all().get_fiches_user_can_view(user).optimized_for_details()
        queryset = queryset.prefetch_related(
            "lieux",
            "lieux__prelevements",
            "lieux__departement",
            "lieux__prelevements__structure_preleveuse",
            "lieux__prelevements__espece_echantillon",
            "lieux__prelevements__matrice_prelevee",
            "lieux__prelevements__laboratoire_agree",
            "lieux__prelevements__laboratoire_confirmation_officielle",
        )
        return queryset

    def get_fieldnames(self):
        empty_prelevement = Prelevement(lieu=Lieu(), structure_preleveuse=StructurePreleveuse())
        return self.get_fiche_data_with_prelevement(FicheDetection(), empty_prelevement).keys()

    def get_fiche_data(self, fiche):
        result = {}
        for field in self.fields:
            result[self._clean_field_name(field, fiche)] = getattr(fiche, field)
        return result

    def get_fiche_data_with_lieu(self, fiche, lieu):
        result = self.get_fiche_data(fiche)
        for field in self.lieux_fields:
            result[self._clean_field_name(field, lieu)] = getattr(lieu, field)
        return result

    def get_fiche_data_with_prelevement(self, fiche, prelevement):
        result = self.get_fiche_data_with_lieu(fiche, prelevement.lieu)
        for field in self.prelevement_fields:
            result[self._clean_field_name(field, prelevement)] = getattr(prelevement, field)
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

    def export(self, stream, user):
        queryset = self.get_queryset(user)
        writer = csv.DictWriter(stream, fieldnames=self.get_fieldnames())
        writer.writeheader()

        for instance in queryset:
            for line in self.get_lines_from_instance(instance):
                writer.writerow(line)
