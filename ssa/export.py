import csv
import tempfile

from django.core.files import File
from django.apps import apps
from queryset_sequence import QuerySetSequence

from core.export import BaseExport
from core.models import Export
from core.notifications import notify_export_is_ready


class SsaExport(BaseExport):
    blank_value = "-"
    evenement_fields = [
        ("numero", "Numéro de fiche"),
        ("etat", "État"),
        ("createur", "Structure créatrice"),
        ("date_creation", "Date de création"),
        ("date_reception", "Date de réception"),
        ("numero_rasff", "Numéro RASFF"),
        ("type_evenement", "Type d'événement"),
        ("source", "Source"),
        ("aliments_animaux", "Inclut des aliments pour animaux"),
        ("description", "Description"),
        ("categorie_produit", "Catégorie de produit"),
        ("denomination", "Dénomination"),
        ("marque", "Marque"),
        ("lots", "Lots, DLC/DDM"),
        ("description_complementaire", "Description complémentaire"),
        ("temperature_conservation", "Température de conservation"),
        ("categorie_danger", "Catégorie de danger"),
        ("precision_danger", "Précision danger"),
        ("quantification", "Quantification"),
        ("quantification_unite", "Unité de quantification"),
        ("evaluation", "Évaluation"),
        ("produit_pret_a_manger", "Produit prêt a manger"),
        ("reference_souches", "Référence souches"),
        ("reference_clusters", "Référence clusters"),
        ("actions_engagees", "Actions engagées"),
        ("numeros_rappel_conso", "Numéro de rappels conso"),
        ("list_of_linked_objects_as_str", "Numéros des objets liés"),
    ]
    etablissement_fields = [
        ("siret", "Numéro SIRET"),
        ("autre_identifiant", "Autre identifiant"),
        ("numero_agrement", "Numéro d'agrément"),
        ("raison_sociale", "Raison sociale"),
        ("enseigne_usuelle", "Enseigne usuelle"),
        ("adresse_lieu_dit", "Adresse ou lieu-dit"),
        ("commune", "Commune"),
        ("departement", "Département"),
        ("pays", "Pays établissement"),
        ("type_exploitant", "Type d'exploitant"),
        ("position_dossier", "Position dans le dossier"),
        ("numeros_resytal", "Numéros d’inspection Resytal"),
    ]

    def get_fieldnames(self):
        return [header for _, header in (self.evenement_fields + self.etablissement_fields)]

    def get_evenement_data(self, instance):
        result = {}
        self.add_data(result, instance, self.evenement_fields)
        return result

    def get_evenement_data_with_etablissement(self, instance, etablissement):
        result = self.get_evenement_data(instance)
        self.add_data(result, etablissement, self.etablissement_fields)
        return result

    def get_lines_from_instance(self, instance):
        etablissements = instance.etablissements.all()
        if not etablissements:
            yield self.get_evenement_data(instance)
            return

        for etablissement in etablissements:
            yield self.get_evenement_data_with_etablissement(instance, etablissement)
            continue

    def get_queryset(self, task):
        querysets = []
        for entry in task.queryset_sequence:
            model = apps.get_model(entry["model"])
            queryset = model.objects.filter(id__in=entry["ids"])
            queryset = queryset.prefetch_related(
                "etablissements",
                "etablissements__departement",
            ).select_related("createur")
            querysets.append(queryset)

        return QuerySetSequence(*querysets)

    def export(self, task_id):
        task = Export.objects.get(id=task_id)
        if task.task_done is True:
            return

        queryset = self.get_queryset(task)
        with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as tmp:
            writer = csv.DictWriter(
                tmp,
                fieldnames=self.get_fieldnames(),
                quoting=csv.QUOTE_ALL,
                doublequote=True,
            )
            writer.writeheader()

            for instance in queryset:
                for line in self.get_lines_from_instance(instance):
                    writer.writerow(line)

            tmp.flush()
            with open(tmp.name, "rb") as read_file:
                task.file.save("export_produit_et_cas.csv", File(read_file))

            task.task_done = True
            task.save()
            notify_export_is_ready(task)
