# Generated by Django 5.0.8 on 2024-11-19 14:41

from django.db import migrations


def remove_oe_prefix(apps, schema_editor):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    nuisibles = OrganismeNuisible.objects.filter(code_oepp__startswith="OE_")
    for nuisible in nuisibles:
        nuisible.code_oepp = nuisible.code_oepp.removeprefix("OE_")
        nuisible.save()


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0039_remove_lieu_code_inpp_etablissement_and_more"),
    ]

    operations = [
        migrations.RunPython(remove_oe_prefix, migrations.RunPython.noop),
    ]
