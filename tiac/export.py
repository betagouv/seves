import csv
from itertools import zip_longest
import tempfile

from django.apps import apps
from django.core.files import File
from queryset_sequence import QuerySetSequence

from core.export import BaseExport
from core.models import Export
from core.notifications import notify_export_is_ready

from .models import EvenementSimple, InvestigationTiac


class TiacExport(BaseExport):
    evenement_fields = [
        ("numero", "Numéro de fiche"),
        ("get_readable_etat_for_csv", "État"),
        ("createur", "Structure créatrice"),
        ("date_creation", "Date de création"),
        ("date_publication", "Date de publication"),
        ("date_reception", "Date de réception"),
        ("evenement_origin", "Signalement déclaré par"),
        ("modalites_declaration", "Modalités de déclaration"),
        ("numero_rasff", "N° RASFF/AAC"),
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
        ("conclusion_repas", " Scénario retenu - Repas"),
        ("conclusion_aliment", " Scénario retenu - Aliment"),
        ("list_of_linked_objects_as_str", "Événements liés"),
    ]

    etablissement_fields = [
        ("siret", "Etablissement - Numéro SIRET"),
        ("numero_agrement", "Etablissement - Numéro d'agrément"),
        ("autre_identifiant", "Etablissement - Autre identifiant"),
        ("raison_sociale", "Etablissement - Raison sociale"),
        ("enseigne_usuelle", "Etablissement - Enseigne usuelle"),
        ("adresse_lieu_dit", "Etablissement - Adresse ou lieu-dit"),
        ("commune_and_cp", "Etablissement - Commune"),
        ("departement", "Etablissement - Département"),
        ("pays", "Etablissement - Pays établissement"),
        ("type_etablissement", "Etablissement - Type d'établissement"),
        ("has_inspection", "Etablissement - Inspection"),
        ("numero_resytal", "Etablissement - Numéro RESYTAL"),
        ("date_inspection", "Etablissement - Date d'inspection"),
        ("evaluation", "Etablissement - Évaluation"),
        ("commentaire", "Etablissement - Commentaire"),
    ]

    repas_fields = [
        ("denomination", "Repas - Dénomination"),
        ("menu", "Repas - Menu"),
        ("motif_suspicion", "Repas - Motif de suspicion du repas"),
        ("datetime_repas", "Repas - Date et heure du repas"),
        ("nombre_participant", "Repas - Nombre de participant(e)s"),
        ("departement", "Repas - Département"),
        ("type_repas", "Repas - Type de repas"),
        ("type_collectivite", "Repas - Type de collectivité"),
    ]

    analyses_fields = [
        ("reference_prelevement", "Analyse - Référence du prélèvement"),
        ("etat_prelevement", "Analyse - État du prélèvement"),
        ("categorie_danger", "Analyse - Catégorie de danger"),
        ("comments", "Analyse - Commentaires liés à l’analyse"),
        ("sent_to_lnr_cnr", "Analyse - Envoyé au LNR/CNR"),
        ("reference_souche", "Analyse - Référence souche"),
    ]

    aliments_fields = [
        ("denomination", "Aliment - Dénomination"),
        ("type_aliment", "Aliment - Type d'aliment"),
        ("description_composition", "Aliment - Description de la composition de l'aliment"),
        ("categorie_produit", "Aliment - Catégorie de produit"),
        ("description_produit", "Aliment - Description produit et emballage"),
        ("motif_suspicion", "Aliment - Motif de suspicion de l'aliment"),
    ]

    def get_fieldnames(self):
        return [
            header
            for _, header in (
                self.evenement_fields
                + self.etablissement_fields
                + self.repas_fields
                + self.aliments_fields
                + self.analyses_fields
            )
        ]

    def get_evenement_data(self, instance, etablissement, repas, aliment, analyse):
        result = {}
        result = self.add_data(result, instance, self.evenement_fields)
        if etablissement:
            result = self.add_data(result, etablissement, self.etablissement_fields)
        if repas:
            result = self.add_data(result, repas, self.repas_fields)
        if aliment:
            result = self.add_data(result, aliment, self.aliments_fields)
        if analyse:
            result = self.add_data(result, analyse, self.analyses_fields)
        return result

    def get_queryset(self, task):
        querysets = []
        for entry in task.queryset_sequence:
            entries = entry["ids"]
            if not entries:
                continue
            model = apps.get_model(entry["model"])
            queryset = model.objects.filter(id__in=entry["ids"])
            contact = task.user.agent.structure.contact_set.get()
            if model == InvestigationTiac:
                queryset = (
                    queryset.prefetch_related(
                        "etablissements",
                        "etablissements__departement",
                        "repas",
                        "repas__departement",
                        "aliments",
                        "analyses_alimentaires",
                    )
                    .select_related("createur")
                    .with_fin_de_suivi(contact)
                )
            else:
                queryset = (
                    queryset.prefetch_related("etablissements", "etablissements__departement")
                    .select_related("createur")
                    .with_fin_de_suivi(contact)
                )
            querysets.append(queryset)
        return QuerySetSequence(*querysets)

    def get_lines_from_instance(self, instance):
        etablissements = instance.etablissements.all()
        if isinstance(instance, EvenementSimple):
            repas, aliments, analyses = [], [], []
        else:
            repas = instance.repas.all()
            aliments = instance.aliments.all()
            analyses = instance.analyses_alimentaires.all()

        if not any([etablissements, repas, aliments, analyses]):
            yield self.get_evenement_data(instance, None, None, None, None)
        else:
            for etablissement, repas, aliment, analyse in zip_longest(etablissements, repas, aliments, analyses):
                yield self.get_evenement_data(instance, etablissement, repas, aliment, analyse)
                continue

    def export(self, task_id):
        task = Export.objects.select_related("user__agent__structure").get(id=task_id)
        if task.task_done is True:
            return

        queryset = self.get_queryset(task)
        fieldnames = self.get_fieldnames()
        with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as tmp:
            writer = csv.DictWriter(
                tmp,
                fieldnames=fieldnames,
                quoting=csv.QUOTE_ALL,
                doublequote=True,
            )
            writer.writeheader()

            for obj in queryset:
                for line in self.get_lines_from_instance(obj):
                    writer.writerow(line)

            tmp.flush()
            with open(tmp.name, "rb") as read_file:
                task.file.save("export_tiac.csv", File(read_file))

            task.task_done = True
            task.save()
            notify_export_is_ready(task, object=queryset[0])
