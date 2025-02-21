# Generated by Django 5.1.4 on 2025-01-23 13:01

from django.db import migrations, models

from sv.organismes_nuisibles import ORGANISMES_NUISIBLES


def add_libelle_long(apps, schema_editor):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")

    for organisme in ORGANISMES_NUISIBLES:
        try:
            existing_object = OrganismeNuisible.objects.get(code_oepp=organisme["code_oepp"])
            existing_object.libelle_court = organisme["libelle_court"]
            existing_object.libelle_long = organisme["libelle_long"]
            existing_object.save()
        except OrganismeNuisible.DoesNotExist:
            OrganismeNuisible.objects.create(**organisme)


class Migration(migrations.Migration):
    dependencies = [
        (
            "sv",
            "0066_remove_fichezonedelimitee_is_deleted_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="organismenuisible",
            name="libelle_long",
            field=models.CharField(max_length=255, null=True, unique=True, verbose_name="Nom"),
        ),
        migrations.RunPython(add_libelle_long, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="organismenuisible",
            name="libelle_long",
            field=models.CharField(max_length=255, unique=True, verbose_name="Nom"),
        ),
    ]
