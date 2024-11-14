from django.core.management.base import BaseCommand
import csv

from core.models import Contact


class Command(BaseCommand):
    help = """
        Ajoute les emails des contacts liés à une structure qui n'ont pas d'email renseigné.
        Les adresses emails sont récupérées depuis le fichier CSV fourni en argument (fichier généré par la commande export_contacts_structures).
        Usage: python manage.py update_contacts_emails contacts_structures.csv
    """

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str)

    def handle(self, *args, **options):
        updates = 0
        with open(options["csv_file"], newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                niveau1 = row["structure (niveau1)"]
                niveau2 = row["structure (niveau2)"]
                email = row["email"].strip()

                if email:
                    updates += Contact.objects.filter(
                        structure__niveau1=niveau1, structure__niveau2=niveau2, email=""
                    ).update(email=email)

        self.stdout.write(f"Mise à jour effectuée : {updates} contacts modifiés")
