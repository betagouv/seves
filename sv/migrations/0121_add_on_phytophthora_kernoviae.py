from django.db import migrations


def add_organisme_nuisible(apps, _):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.get_or_create(
        code_oepp="PHYTKE",
        defaults={"libelle_court": "Phytophthora kernoviae", "libelle_long": "Phytophthora kernoviae"},
    )


def reverse_add_organisme_nuisible(apps, _):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.filter(code_oepp="PHYTKE").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0120_auto_20260424_1058"),
    ]

    operations = [
        migrations.RunPython(add_organisme_nuisible, reverse_add_organisme_nuisible),
    ]
