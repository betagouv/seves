from django.db import migrations


def add_on(apps, schema_editor):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.get_or_create(
        code_oepp="PAPIDD",
        libelle_court="Papilio demodocus",
        defaults={
            "libelle_long": "Papilio demodocus",
        },
    )


def reverse_add_on(apps, schema_editor):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.filter(code_oepp="PAPIDD", libelle_court="Papilio demodocus").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0134_alter_lieu_code_insee_etablissement"),
    ]

    operations = [
        migrations.RunPython(add_on, reverse_add_on),
    ]
