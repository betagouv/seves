# Generated by Django 5.0.8 on 2024-11-15 14:06

from django.db import migrations


def add_new_status(apps, schema_editor):
    StatutReglementaire = apps.get_model("sv", "StatutReglementaire")
    StatutReglementaire.objects.get_or_create(code="OTR", libelle="organisme temporairement réglementé")
    StatutReglementaire.objects.get_or_create(code="OE", libelle="organisme émergent")


class Migration(migrations.Migration):
    dependencies = [
        (
            "sv",
            "0036_remove_fichezonedelimitee_caracteristiques_principales_zone_delimitee_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(add_new_status, migrations.RunPython.noop),
    ]
