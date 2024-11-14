from django.core.management.base import BaseCommand
import csv
import sys

from core.models import Structure


class Command(BaseCommand):
    help = """
        Exporte tous les contacts reliés à une structure.
        Usage: python manage.py export_contacts_structures > contacts_structures.csv
    """

    def handle(self, *args, **options):
        writer = csv.writer(sys.stdout, delimiter=";")
        writer.writerow(["structure (niveau1)", "structure (niveau2)", "email"])
        for structure in Structure.objects.filter(contact__email=""):
            writer.writerow([structure.niveau1, structure.niveau2, ""])
