from pathlib import Path

from django.core.management.base import BaseCommand
import csv
from typing import Set

from seves import settings


class Command(BaseCommand):
    help = "Extrait les structures uniques d'un fichier CSV (export Agricoll) pour générer un fichier de structures autorisées"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path", type=str, help="Chemin vers le fichier CSV source contenant les contacts (export Agricoll)"
        )
        parser.add_argument(
            "output_path",
            type=str,
            help="Chemin vers le fichier Python à générer contenant les structures autorisées",
        )

    def should_include_structure(self, structure: str) -> bool:
        """
        Population à extraire :
            - AC/DAC/DGAL*
            - SD/*/SRAL*
            - SD/DRAAF/*/DIRECTION
            - SD/DAAF*
            - DDI/DDPP/*
            - DDETSPP
        """
        rules = [
            structure.startswith("AC/DAC/DGAL"),
            structure.startswith("SD/") and "SRAL" in structure,
            structure.startswith("SD/DRAAF/") and "DIRECTION" in structure,
            structure.startswith("SD/DAAF"),
            structure.startswith("DDI/DDPP/"),
            structure.startswith("DDETSPP"),
        ]
        return any(rules)

    def extract_structures(self, csv_path: str) -> Set[str]:
        """Extrait les structures uniques du fichier CSV."""
        unique_structures = set()

        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            next(reader, None)  # Ignore l'en-tête

            for row in reader:
                structure = row["Structure"].strip()
                if structure and self.should_include_structure(structure):
                    unique_structures.add(structure)

        return unique_structures

    def write_structures_file(self, structures: Set[str], output_path: str) -> Path:
        with open(output_path, "w", encoding="utf-8") as pyfile:
            pyfile.write("ALLOWED_STRUCTURES = {\n")
            for structure in sorted(structures):
                pyfile.write(f'    "{structure}",\n')
            pyfile.write("}\n")

    def handle(self, *args, **options):
        try:
            csv_path = options["csv_path"]
            output_path = options["output_path"]

            self.stdout.write(self.style.NOTICE(f"Lecture du fichier {csv_path}..."))

            structures = self.extract_structures(csv_path)
            self.write_structures_file(structures, output_path)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Le fichier structures.py a été généré avec succès dans '{Path(settings.BASE_DIR)}/{output_path}' ({len(structures)} structures extraites)."
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Une erreur est survenue : {str(e)}"))
            raise
