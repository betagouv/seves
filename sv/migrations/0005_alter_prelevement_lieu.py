# Generated by Django 5.0.3 on 2024-05-02 20:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0004_remove_prelevementofficiel_espece_echantillon_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prelevement",
            name="lieu",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prelevements",
                to="sv.lieu",
                verbose_name="Lieu",
            ),
        ),
    ]
