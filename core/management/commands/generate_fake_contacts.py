import csv
from itertools import islice

from django.core.management.base import BaseCommand
from faker import Faker

fake = Faker("fr_FR")


class Command(BaseCommand):
    help = "Anonymise les contacts du fichier CSV d'entrée avec des données fictives mais réalistes et exporte le résultat dans un nouveau fichier CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "input_file", type=str, help="Chemin vers le fichier CSV d'entrée (export fichier de contacts AGRICOLL)"
        )
        parser.add_argument("--count", type=int, help="Nombre de contacts à anonymiser", default=None)

    def handle(self, *args, **kwargs):
        input_file = kwargs["input_file"]
        count = kwargs["count"]
        output_file = "fake_contacts.csv"

        with open(input_file, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file, delimiter=";")

            with open(output_file, mode="w", newline="", encoding="utf-8") as new_file:
                writer = csv.writer(new_file, delimiter=";")
                headers = next(reader)  # Lecture et écriture des en-têtes dans le nouveau fichier
                writer.writerow(headers)

                rows = islice(reader, count) if count is not None else reader

                for row in rows:
                    fake_first_name = fake.first_name()
                    fake_last_name = fake.last_name()
                    fake_email = f"{fake_first_name.lower()}.{fake_last_name.lower()}@example.com"
                    fake_fixed_phone = (
                        f"+33 {fake.random_element(elements=('1', '2', '3', '4', '5'))} {fake.numerify('## ## ## ##')}"
                    )
                    fake_mobile_phone = f"+33 {fake.random_element(elements=('6', '7'))} {fake.numerify('## ## ## ##')}"

                    row[1], row[2], row[3], row[6], row[7] = (
                        fake_first_name,
                        fake_last_name,
                        fake_email,
                        fake_fixed_phone,
                        fake_mobile_phone,
                    )
                    writer.writerow(row)

                message = "Toutes les données" if count is None else f"Les {count} premières données"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{message} ont été anonymisées et enregistrées avec succès dans le fichier {output_file}"
                    )
                )
