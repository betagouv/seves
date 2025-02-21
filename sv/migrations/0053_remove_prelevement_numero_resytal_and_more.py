# Generated by Django 5.1.2 on 2024-12-12 16:19

import sv.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0052_alter_zoneinfestee_unite_surface_infestee_totale"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="prelevement",
            name="numero_resytal",
        ),
        migrations.AddField(
            model_name="prelevement",
            name="numero_rapport_inspection",
            field=models.CharField(
                blank=True,
                max_length=9,
                validators=[sv.models.validate_numero_rapport_inspection],
                verbose_name="Numéro du rapport d'inspection",
            ),
        ),
    ]
