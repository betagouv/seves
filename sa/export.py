import csv
import tempfile

from django.core.files import File

from core.export import BaseExport
from core.models import Export
from core.notifications import notify_export_is_ready
from sa.models import EvenementAnimal


class SaExport(BaseExport):
    evenement_fields = [
        ("numero", "Numéro de fiche"),
        ("get_readable_etat_for_csv", "État"),
        ("createur", "Structure créatrice"),
        ("date_creation", "Date de création"),
    ]

    def get_fieldnames(self):
        return [header for _, header in (self.evenement_fields)]

    def get_evenement_data(self, instance):
        result = {}
        result = self.add_data(result, instance, self.evenement_fields)
        return result

    def get_queryset(self, task):
        contact = task.user.agent.structure.contact_set.get()
        return (
            EvenementAnimal.objects.filter(id__in=task.object_ids).select_related("createur").with_fin_de_suivi(contact)
        )

    def get_lines_from_instance(self, instance):
        yield self.get_evenement_data(instance)

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
                task.file.save("export_sa.csv", File(read_file))

            task.task_done = True
            task.save()
            notify_export_is_ready(task, object=queryset[0])
