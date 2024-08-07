# Generated by Django 5.0.3 on 2024-08-01 14:31

import django.db.models.deletion
from django.db import migrations, models


def add_createur_structure_to_all_existing_fichedetection(apps, schema_editor):
    FicheDetection = apps.get_model("sv", "FicheDetection")
    Structure = apps.get_model("core", "Structure")

    for fiche in FicheDetection.objects.all():
        fiche.createur_structure = Structure.objects.first()
        fiche.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_alter_contact_agent_alter_contact_structure"),
        ("sv", "0011_prelevement_resultat"),
    ]

    operations = [
        migrations.AddField(
            model_name="fichedetection",
            name="createur_structure",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="core.structure",
                verbose_name="Structure créatrice",
            ),
        ),
        migrations.RunPython(add_createur_structure_to_all_existing_fichedetection),
    ]
