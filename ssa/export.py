import csv
import tempfile

from django.core.files import File

from core.models import Export
from core.notifications import notify_export_is_ready
from ssa.models import EvenementProduit


class EvenementProduitExport:
    evenement_produit_fields = [
        ("numero_annee", "Année"),
        ("numero_evenement", "Numéro"),
        ("createur", "Structure créatrice"),
        ("date_creation", "Date de création"),
        ("numero_rasff", "Numéro RASFF"),
        ("type_evenement", "Type d'événement"),
        ("source", "Source"),
        ("description", "Description"),
        ("categorie_produit", "Catégorie de produit"),
        ("denomination", "Dénomination"),
        ("marque", "Marque"),
        ("lots", "Lots, DLC/DDM"),
        ("description_complementaire", "Description complémentaire"),
        ("temperature_conservation", "Température de conservation"),
        ("categorie_danger", "Catégorie de danger"),
        ("quantification", "Quantification"),
        ("quantification_unite", "Unité de quantification"),
        ("evaluation", "Évaluation"),
        ("produit_pret_a_manger", "Produit prêt a manger"),
        ("reference_souches", "Référence souches"),
        ("reference_clusters", "Référence clusters"),
        ("actions_engagees", "Actions engagées"),
        ("numeros_rappel_conso", "Numéro de rappels conso"),
    ]
    etablissement_fields = [
        ("siret", "Numéro SIRET"),
        ("raison_sociale", "Raison sociale"),
        ("adresse_lieu_dit", "Adresse ou lieu-dit"),
        ("commune", "Commune"),
        ("departement", "Département"),
        ("pays", "Pays établissement"),
        ("type_exploitant", "Type d'exploitant"),
        ("position_dossier", "Position dans le dossier"),
    ]

    def get_fieldnames(self):
        return [header for _, header in (self.evenement_produit_fields + self.etablissement_fields)]

    def get_field_value(self, instance, field):
        attrs = field.split("__")
        for i, attr in enumerate(attrs):
            is_last_level_attribute = len(attrs) - 1
            if i == is_last_level_attribute:
                display_method = f"get_{attr}_display"
                if hasattr(instance, display_method):
                    return getattr(instance, display_method)()
            value = getattr(instance, attr, None)
            if isinstance(value, list):
                return ",".join(value) if value else None
            return value

    def add_data(self, result, instance, fields):
        for field, header in fields:
            result[header] = self.get_field_value(instance, field)
        return result

    def get_evenement_data(self, evenement_produit):
        result = {}
        self.add_data(result, evenement_produit, self.evenement_produit_fields)
        return result

    def get_evenement_data_with_etablissement(self, evenement_produit, etablissement):
        result = self.get_evenement_data(evenement_produit)
        self.add_data(result, etablissement, self.etablissement_fields)
        return result

    def get_lines_from_instance(self, evenement_produit):
        etablissements = evenement_produit.etablissements.all()
        if not etablissements:
            yield self.get_evenement_data(evenement_produit)
            return

        for etablissement in etablissements:
            yield self.get_evenement_data_with_etablissement(evenement_produit, etablissement)
            continue

    def export(self, task_id):
        task = Export.objects.get(id=task_id)
        if task.task_done is True:
            return

        queryset = (
            EvenementProduit.objects.filter(id__in=task.object_ids)
            .select_related("createur")
            .prefetch_related("etablissements")
        )
        obj_id_to_obj = {obj.id: obj for obj in queryset}
        ordered_objs = [obj_id_to_obj[i] for i in task.object_ids if i in obj_id_to_obj]

        with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as tmp:
            writer = csv.DictWriter(
                tmp,
                fieldnames=self.get_fieldnames(),
                quoting=csv.QUOTE_ALL,
                doublequote=True,
            )
            writer.writeheader()

            for instance in ordered_objs:
                for line in self.get_lines_from_instance(instance):
                    writer.writerow(line)

            tmp.flush()
            with open(tmp.name, "rb") as read_file:
                task.file.save("export_evenement_produit.csv", File(read_file))

            task.task_done = True
            task.save()
            notify_export_is_ready(task)
