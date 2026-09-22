from django.db import migrations


def add_on(apps, schema_editor):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.get_or_create(
        code_oepp="XYLORF",
        libelle_court="Xylotrechus rufilius",
        defaults={
            "libelle_long": "Xylotrechus rufilius",
        },
    )


def reverse_add_on(apps, schema_editor):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.filter(code_oepp="XYLORF", libelle_court="Xylotrechus rufilius").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0131_auto_20260911_1432"),
    ]

    operations = [
        migrations.RunPython(add_on, reverse_add_on),
    ]
