import csv
from functools import reduce

from .models import FicheDetection


class FicheDetectionExport:
    fiche_detection_fields = [
        ("numero", "Numéro de fiche"),
        ("evenement__numero", "Num. événement"),
        ("evenement__organisme_nuisible__libelle_court", "Organisme nuisible"),
        ("evenement__organisme_nuisible__code_oepp", "Code OEPP"),
        ("evenement__statut_reglementaire__libelle", "Statut réglementaire"),
        ("evenement__numero_europhyt", "Numéro Europhyt"),
        ("evenement__numero_rasff", "Numéro RASFF"),
        ("date_creation", "Date de création"),
        ("createur", "Structure créatrice"),
        ("statut_evenement", "Statut de l'événement"),
        ("contexte", "Contexte"),
        ("vegetaux_infestes", "Nombre ou volume de végétaux infestés"),
        ("date_premier_signalement", "Date premier signalement"),
        ("commentaire", "Commentaire"),
        ("mesures_conservatoires_immediates", "Mesures conservatoires immédiates"),
        ("mesures_consignation", "Mesures de consignation"),
        ("mesures_phytosanitaires", "Mesures phytosanitaires"),
        ("mesures_surveillance_specifique", "Mesures de surveillance spécifique"),
    ]
    lieux_fields = [
        ("nom", "Nom"),
        ("adresse_lieu_dit", "Adresse ou lieu-dit"),
        ("commune", "Commune"),
        ("site_inspection", "Site d'inspection"),
        ("wgs84_longitude", "Longitude WGS84"),
        ("wgs84_latitude", "Latitude WGS84"),
        ("activite_etablissement", "Activité établissement"),
        ("pays_etablissement", "Pays établissement"),
        ("raison_sociale_etablissement", "Raison sociale établissement"),
        ("adresse_etablissement", "Adresse établissement"),
        ("siret_etablissement", "SIRET établissement"),
        ("code_inupp_etablissement", "Code INUPP"),
    ]
    prelevement_fields = [
        ("type_analyse", "Type d'analyse"),
        ("is_officiel", "Prélèvement officiel"),
        ("numero_rapport_inspection", "Numéro du rapport d'inspection"),
        ("laboratoire", "Laboratoire"),
        ("numero_echantillon", "N° d'échantillon"),
        ("structure_preleveuse", "Structure préleveuse"),
        ("date_prelevement", "Date de prélèvement"),
        ("matrice_prelevee", "Nature de l'objet"),
        ("espece_echantillon", "Espèce de l'échantillon"),
        ("resultat", "Résultat"),
    ]
    fiche_zone_delimitee_fields = [
        ("evenement__fiche_zone_delimitee__commentaire", "Commentaire zone délimitée"),
        ("evenement__fiche_zone_delimitee__rayon_zone_tampon", "Rayon tampon réglementaire ou arbitré"),
        ("evenement__fiche_zone_delimitee__surface_tampon_totale", "Surface tampon totale"),
    ]
    zone_infestee_fields = [
        ("zone_infestee__nom", "Nom de la zone infestée"),
        ("zone_infestee__caracteristique_principale", "Caractéristique principale"),
        ("zone_infestee__rayon", "Rayon de la zone infestée"),
        ("zone_infestee__surface_infestee_totale", "Surface infestée totale"),
    ]

    def get_queryset(self, user):
        return (
            FicheDetection.objects.all()
            .get_fiches_user_can_view(user)
            .optimized_for_details()
            .select_related(
                "evenement__organisme_nuisible",
                "evenement__statut_reglementaire",
            )
            .prefetch_related(
                "lieux",
                "lieux__departement",
                "lieux__site_inspection",
                "lieux__prelevements",
                "lieux__prelevements__structure_preleveuse",
                "lieux__prelevements__espece_echantillon",
                "lieux__prelevements__matrice_prelevee",
                "lieux__prelevements__laboratoire",
            )
        )

    def get_fieldnames(self):
        """Retourne les noms des champs pour l'en-tête du CSV"""
        all_fields = (
            self.fiche_detection_fields
            + self.lieux_fields
            + self.prelevement_fields
            + self.fiche_zone_delimitee_fields
            + self.zone_infestee_fields
        )
        return [header for _, header in all_fields]

    def get_field_value(self, instance, field):
        """Récupère et formate la valeur d'un champ, en suivant les relations Django si nécessaire."""
        return reduce(lambda obj, attr: getattr(obj, attr, None) if obj else None, field.split("__"), instance)

    def add_data(self, result, instance, fields):
        for field, header in fields:
            result[header] = self.get_field_value(instance, field)
        return result

    def add_fiche_detection_data(self, result, fiche):
        return self.add_data(result, fiche, self.fiche_detection_fields)

    def add_lieu_data(self, result, lieu):
        return self.add_data(result, lieu, self.lieux_fields)

    def add_prelevement_data(self, result, prelevement):
        return self.add_data(result, prelevement, self.prelevement_fields)

    def add_zone_delimitee_data(self, result, fiche):
        return self.add_data(result, fiche, self.fiche_zone_delimitee_fields)

    def add_zone_infestee_data(self, result, fiche):
        return self.add_data(result, fiche, self.zone_infestee_fields)

    def get_fiche_data(self, fiche):
        result = {}
        self.add_fiche_detection_data(result, fiche)
        self.add_zone_delimitee_data(result, fiche)
        self.add_zone_infestee_data(result, fiche)
        return result

    def get_fiche_data_with_lieu(self, fiche, lieu):
        result = {}
        self.add_fiche_detection_data(result, fiche)
        self.add_lieu_data(result, lieu)
        self.add_zone_delimitee_data(result, fiche)
        self.add_zone_infestee_data(result, fiche)
        return result

    def get_fiche_data_with_prelevement(self, fiche, prelevement):
        result = {}
        self.add_fiche_detection_data(result, fiche)
        self.add_lieu_data(result, prelevement.lieu)
        self.add_prelevement_data(result, prelevement)
        self.add_zone_delimitee_data(result, fiche)
        self.add_zone_infestee_data(result, fiche)
        return result

    def get_lines_from_instance(self, fiche_detection):
        lieux = fiche_detection.lieux.all()
        if not lieux:
            yield self.get_fiche_data(fiche_detection)
            return

        for lieu in lieux:
            prelevements = lieu.prelevements.all()
            if not prelevements:
                yield self.get_fiche_data_with_lieu(fiche_detection, lieu)
                continue

            for prelevement in prelevements:
                yield self.get_fiche_data_with_prelevement(fiche_detection, prelevement)

    def export(self, stream, user):
        queryset = self.get_queryset(user)
        writer = csv.DictWriter(
            stream,
            fieldnames=self.get_fieldnames(),
            quoting=csv.QUOTE_ALL,
            doublequote=True,
        )
        writer.writeheader()

        for instance in queryset:
            for line in self.get_lines_from_instance(instance):
                writer.writerow(line)
