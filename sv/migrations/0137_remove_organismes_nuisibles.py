from django.db import migrations

ORGANISMES_NUISIBLES = {
    "ACIEKA": "Acidiella kagoshimensis",
    "ACIXBO": "Acidoxantha bombacis",
    "CLMYFL": "Callistomyia flavilabris",
    "EPHNOS": "Euphranta oshimensis",
    "GASZNI": "Gastrozona nigrifemur",
    "INZWOB": "Insizwa oblita",
    "PTEPFU": "Paratephritis fukaii",
    "PTEPTA": "Paratephritis takeuchii",
    "URORCH": "Urophora christophi",
}


def remove_organismes_nuisibles(apps, _):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.filter(code_oepp__in=ORGANISMES_NUISIBLES).delete()


def readd_organismes_nuisibles(apps, _):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    for code_oepp, libelle in ORGANISMES_NUISIBLES.items():
        OrganismeNuisible.objects.get_or_create(code_oepp=code_oepp, libelle_court=libelle, libelle_long=libelle)


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0136_auto_20261009_0843"),
    ]

    operations = [migrations.RunPython(remove_organismes_nuisibles, reverse_code=readd_organismes_nuisibles)]
