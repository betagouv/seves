import csv

from django.core.management.base import BaseCommand

from sv.models import EspeceEchantillon


class Command(BaseCommand):
    help = "Permet l'import des espèces et des code OEPP depuis un fichier CSV."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str)

    def handle(self, *args, **options):
        with open(options["file"]) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            especes = [
                EspeceEchantillon(code_oepp=row["vegetalCodeOeppLb"], libelle=row["vegetalCourtLb"]) for row in reader
            ]
            EspeceEchantillon.objects.bulk_create(especes)
