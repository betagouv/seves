import time
from django.db.utils import DataError
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
import csv
from core.models import Contact, Structure, Agent


class Command(BaseCommand):
    help = "Importe des contacts à partir d'un fichier CSV (export Agricoll)"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Le chemin vers le fichier CSV à importer")

    def clean_contacts_data(self, reader: csv.DictReader):
        """ignore les contacts dont l'email est inconnu"""
        for row in reader:
            if not row["Mail"].strip().lower() == "inconnu":
                yield row

    def save_contact(self, row, ligne):
        try:
            # Contact pour structure
            parts = row["Structure"].split("/")
            niveau1 = ""
            niveau2 = ""

            if row["Structure"].startswith("AC/DAC/DGAL"):
                niveau1 = "/".join(parts[:3])
                niveau2 = "/".join(parts[3:])
            elif row["Structure"].startswith(("SD/DRAAF", "SD/DAAF", "DDI/DDPP", "DDI/DDETSPP")):
                niveau1 = "/".join(parts[:2])
                niveau2 = parts[2]

            if not niveau1:
                return

            structure, _ = Structure.objects.get_or_create(
                niveau1=niveau1, niveau2=niveau2, defaults={"libelle": niveau2 or niveau1}
            )

            Contact.objects.get_or_create(structure=structure)

            # Contact pour agent
            User = get_user_model()
            user, _ = User.objects.get_or_create(username=row["Mail"], email=row["Mail"], defaults={"is_active": False})

            agent, _ = Agent.objects.update_or_create(
                user=user,
                defaults={
                    "structure": structure,
                    "structure_complete": row["Structure"],
                    "prenom": row["Prénom"],
                    "nom": row["Nom"],
                    "fonction_hierarchique": row.get("Fonction_hiérarchique", ""),
                    "complement_fonction": row.get("Complément_fonction", ""),
                    "telephone": row.get("Téléphone", ""),
                    "mobile": row.get("Mobile", ""),
                },
            )

            Contact.objects.update_or_create(
                agent=agent,
                defaults={
                    "email": row["Mail"],
                },
            )
        except DataError as e:
            raise Exception(f"Erreur lors de l'importation à la ligne {ligne} : {e}")

    def handle(self, *args, **kwargs):
        self.stdout.write("Début de l'importation...")
        start_time = time.time()
        csv_file_path = kwargs["csv_file"]
        ligne = 1
        with open(csv_file_path, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=",")
            with transaction.atomic():
                for row in self.clean_contacts_data(reader):
                    ligne += 1
                    self.save_contact(row, ligne)
        end_time = time.time()
        self.stdout.write(self.style.SUCCESS(f"Importation terminée en {int(end_time - start_time)} secondes"))
