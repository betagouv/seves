from django.db import migrations


def add_on(apps, schema_editor):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.get_or_create(
        code_oepp="PODNQU",
        libelle_court="Podontia quatuordecimpunctata",
        defaults={
            "libelle_long": "Podontia quatuordecimpunctata",
        },
    )


def reverse_add_on(apps, schema_editor):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.filter(code_oepp="PODNQU", libelle_court="Podontia quatuordecimpunctata").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0138_auto_20261109_1516"),
    ]

    operations = [
        migrations.RunPython(add_on, reverse_add_on),
    ]
