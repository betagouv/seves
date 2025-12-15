import csv
import tempfile

from django.apps import apps
from django.core.files import File
from django.db.models import Count, Max
from queryset_sequence import QuerySetSequence

from core.export import BaseExport
from core.models import Export
from core.notifications import notify_export_is_ready
from .models import InvestigationTiac


class TiacExport(BaseExport):
    REPAS_KEY = "Repas"
    ETABLISSEMENT_KEY = "Etablissement"
    ALIMENT_KEY = "Aliment"
    ANALYSE_KEY = "Analyse alimentaire"

    evenement_fields = [
        ("numero", "Numéro de fiche"),
        ("etat", "État"),
        ("createur", "Structure créatrice"),
        ("date_creation", "Date de création"),
        ("date_reception", "Date de réception"),
        ("evenement_origin", "Signalement déclaré par"),
        ("modalites_declaration", "Modalités de déclaration"),
        ("contenu", "Contenu du signalement"),
        ("notify_ars", "ARS informée"),
        ("will_trigger_inquiry", "Enquête auprès des cas"),
        ("numero_sivss", "N° SIVSS de l'ARS"),
        ("type_evenement", "Type d'événement"),
        ("follow_up", "Suite donnée"),
        ("transfered_to", "Transféré à"),
        ("nb_sick_persons", "Nombre de malades total"),
        ("nb_sick_persons_to_hospital", "Dont conduits à l'hôpital"),
        ("nb_dead_persons", "Dont décédés"),
        ("datetime_first_symptoms", "Première date et heure d'apparition des symptômes"),
        ("datetime_last_symptoms", "Dernière date et heure d'apparition des symptômes"),
        ("danger_syndromiques_suspectes", "Danger syndromique suspectés"),
        ("analyses_sur_les_malades", "Analyses engagées sur les malades"),
        ("precisions", "Précisions"),
        ("agents_confirmes_ars", "Agent pathogènes confirmés par l'ARS"),
        ("suspicion_conclusion", "Conclusion de la suspicion de TIAC"),
        ("selected_hazard", "Dangers retenus"),
        ("conclusion_comment", "Commentaire"),
        ("conclusion_etablissement", " Scénario retenu - Établissement"),
        ("conclusion_repas", " Scénario retenu - Repas"),
        ("conclusion_aliment", " Scénario retenu - Aliment"),
        ("conclusion_analyse", " Scénario retenu - Analyse"),
        ("list_of_linked_objects_as_str", "Événements liés"),
    ]

    etablissement_fields = [
        ("siret", "Numéro SIRET"),
        ("autre_identifiant", "Autre identifiant"),
        ("raison_sociale", "Raison sociale"),
        ("enseigne_usuelle", "Enseigne usuelle"),
        ("adresse_lieu_dit", "Adresse ou lieu-dit"),
        ("commune", "Commune"),
        ("departement", "Département"),
        ("pays", "Pays établissement"),
        ("type_etablissement", "Type d'établissement"),
        ("has_inspection", "Inspection"),
        ("numero_resytal", "Numéro RESYTAL"),
        ("date_inspection", "Date d'inspection"),
        ("evaluation", "Évaluation"),
        ("commentaire", "Commentaire"),
    ]

    repas_fields = [
        ("denomination", "Dénomination"),
        ("menu", "Menu"),
        ("motif_suspicion", "Motif de suspicion du repas"),
        ("datetime_repas", "Date et heure du repas"),
        ("nombre_participant", "Nombre de participant(e)s"),
        ("departement", "Département"),
        ("type_repas", "Type de repas"),
        ("type_collectivite", "Type de collectivité"),
    ]

    analyses_fields = [
        ("reference_prelevement", "Référence du prélèvement"),
        ("etat_prelevement", "État du prélèvement"),
        ("categorie_danger", "Catégorie de danger"),
        ("comments", "Commentaires liés à l’analyse"),
        ("sent_to_lnr_cnr", "Envoyé au LNR/CNR"),
        ("reference_souche", "Référence souche"),
    ]

    aliments_fields = [
        ("denomination", "Dénomination"),
        ("type_aliment", "Type d'aliment"),
        ("description_composition", "Description de la composition de l'aliment"),
        ("categorie_produit", "Catégorie de produit"),
        ("description_produit", "Description produit et emballage"),
        ("motif_suspicion", "Motif de suspicion de l'aliment"),
    ]

    def get_fieldnames(self, nb_etablissement, nb_repas, nb_aliment, nb_prelevement):
        base_headers = [header for _, header in self.evenement_fields]
        etablissement_headers = [f"{self.ETABLISSEMENT_KEY} {i}" for i in range(1, nb_etablissement + 1)]
        repas_headers = [f"{self.REPAS_KEY} {i}" for i in range(1, nb_repas + 1)]
        aliment_headers = [f"{self.ALIMENT_KEY} {i}" for i in range(1, nb_aliment + 1)]
        prelevement_headers = [f"{self.ANALYSE_KEY} {i}" for i in range(1, nb_prelevement + 1)]
        return base_headers + etablissement_headers + repas_headers + aliment_headers + prelevement_headers

    def get_related_object_as_str(self, obj, fields):
        lines = []
        for field, display_name in fields:
            lines.append(f"{display_name} : {self.get_field_value(obj, field)}")
        return "\n".join(lines)

    def get_data_from_instance(self, object):
        result = {}
        self.add_data(result, object, self.evenement_fields)
        for idx, related_obj in enumerate(object.etablissements.all()):
            result[f"{self.ETABLISSEMENT_KEY} {idx + 1}"] = self.get_related_object_as_str(
                related_obj, self.etablissement_fields
            )
        try:
            for idx, related_obj in enumerate(object.repas.all()):
                result[f"{self.REPAS_KEY} {idx + 1}"] = self.get_related_object_as_str(related_obj, self.repas_fields)
            for idx, related_obj in enumerate(object.analyses_alimentaires.all()):
                result[f"{self.ANALYSE_KEY} {idx + 1}"] = self.get_related_object_as_str(
                    related_obj, self.analyses_fields
                )
            for idx, related_obj in enumerate(object.aliments.all()):
                result[f"{self.ALIMENT_KEY} {idx + 1}"] = self.get_related_object_as_str(
                    related_obj, self.aliments_fields
                )
        except AttributeError:
            pass  # EvenementSimple object does not have those related fields
        return result

    def get_queryset_and_nb_objects(self, task):
        querysets = []
        max_etablissement = max_repas = max_aliment = max_analyses = 0
        for entry in task.queryset_sequence:
            entries = entry["ids"]
            if not entries:
                continue
            model = apps.get_model(entry["model"])
            queryset = model.objects.filter(id__in=entry["ids"])
            if model == InvestigationTiac:
                queryset = queryset.prefetch_related(
                    "etablissements",
                    "etablissements__departement",
                    "repas",
                    "repas__departement",
                    "aliments",
                    "analyses_alimentaires",
                ).select_related("createur")
            else:
                queryset = queryset.prefetch_related("etablissements", "etablissements__departement").select_related(
                    "createur"
                )

            querysets.append(queryset)
            if model == InvestigationTiac:
                queryset = queryset.annotate(
                    nb_repas=Count("repas", distinct=True),
                    nb_aliment=Count("aliments", distinct=True),
                    nb_analyses=Count("analyses_alimentaires", distinct=True),
                    nb_etablissement=Count("etablissements", distinct=True),
                ).aggregate(
                    max_repas=Max("nb_repas"),
                    max_aliment=Max("nb_aliment"),
                    max_analyses=Max("nb_analyses"),
                    max_etablissements=Max("nb_etablissement"),
                )
                max_repas = queryset["max_repas"]
                max_aliment = queryset["max_aliment"]
                max_analyses = queryset["max_analyses"]
            else:
                queryset = queryset.annotate(
                    nb_etablissement=Count("etablissements", distinct=True),
                ).aggregate(
                    max_etablissements=Max("nb_etablissement"),
                )

            if queryset["max_etablissements"] > max_etablissement:
                max_etablissement = queryset["max_etablissements"]

        queryset = QuerySetSequence(*querysets)
        return queryset, max_etablissement, max_repas, max_aliment, max_analyses

    def export(self, task_id):
        task = Export.objects.get(id=task_id)
        if task.task_done is True:
            return

        queryset, max_etablissement, max_repas, max_aliment, max_analyses = self.get_queryset_and_nb_objects(task)
        fieldnames = self.get_fieldnames(max_etablissement, max_repas, max_aliment, max_analyses)
        with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as tmp:
            writer = csv.DictWriter(
                tmp,
                fieldnames=fieldnames,
                quoting=csv.QUOTE_ALL,
                doublequote=True,
            )
            writer.writeheader()

            for obj in queryset:
                writer.writerow(self.get_data_from_instance(obj))

            tmp.flush()
            with open(tmp.name, "rb") as read_file:
                task.file.save("export_tiac.csv", File(read_file))

            task.task_done = True
            task.save()
            notify_export_is_ready(task)
