import time
from django.db.utils import DataError
from django.core.management.base import BaseCommand
from django.db import transaction
import csv
from core.models import Contact


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
            Contact.objects.update_or_create(
                email=row["Mail"],
                defaults={
                    "structure": row["Structure"],
                    "prenom": row["Prénom"],
                    "nom": row["Nom"],
                    "fonction_hierarchique": row.get("Fonction_hiérarchique", ""),
                    "complement_fonction": row.get("Complément_fonction", ""),
                    "telephone": row.get("Téléphone", ""),
                    "mobile": row.get("Mobile", ""),
                },
            )
        except DataError as e:
            raise Exception(f"Erreur lors de l'importation à la ligne {ligne} : {e}")

    def handle(self, *args, **kwargs):
        temps_debut = time.time()
        csv_file_path = kwargs["csv_file"]
        ligne = 1
        with open(csv_file_path, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=";")
            with transaction.atomic():
                for row in self.clean_contacts_data(reader):
                    ligne += 1
                    self.save_contact(row, ligne)
        temps_fin = time.time()
        self.stdout.write(self.style.SUCCESS(f"Importation terminée en {int(temps_fin - temps_debut)} secondes"))
