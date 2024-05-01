# Generated by Django 5.0.3 on 2024-05-01 12:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0003_remove_prelevementnonofficiel_fiche_detection_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="prelevementofficiel",
            name="espece_echantillon",
        ),
        migrations.RemoveField(
            model_name="prelevementofficiel",
            name="laboratoire_agree",
        ),
        migrations.RemoveField(
            model_name="prelevementofficiel",
            name="laboratoire_confirmation_officielle",
        ),
        migrations.RemoveField(
            model_name="prelevementofficiel",
            name="lieu",
        ),
        migrations.RemoveField(
            model_name="prelevementofficiel",
            name="matrice_prelevee",
        ),
        migrations.RemoveField(
            model_name="prelevementofficiel",
            name="site_inspection",
        ),
        migrations.RemoveField(
            model_name="prelevementofficiel",
            name="structure_preleveur",
        ),
        migrations.CreateModel(
            name="Prelevement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "numero_echantillon",
                    models.CharField(blank=True, max_length=100, verbose_name="Numéro d'échantillon"),
                ),
                ("date_prelevement", models.DateField(blank=True, null=True, verbose_name="Date de prélèvement")),
                ("is_officiel", models.BooleanField(default=False, verbose_name="Prélèvement officiel")),
                ("numero_phytopass", models.CharField(blank=True, max_length=100, verbose_name="Numéro Phytopass")),
                (
                    "espece_echantillon",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.especeechantillon",
                        verbose_name="Espèce de l'échantillon",
                    ),
                ),
                (
                    "laboratoire_agree",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.laboratoireagree",
                        verbose_name="Laboratoire agréé",
                    ),
                ),
                (
                    "laboratoire_confirmation_officielle",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.laboratoireconfirmationofficielle",
                        verbose_name="Laboratoire de confirmation officielle",
                    ),
                ),
                (
                    "lieu",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="sv.lieu", verbose_name="Lieu"),
                ),
                (
                    "matrice_prelevee",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.matriceprelevee",
                        verbose_name="Matrice prélevée",
                    ),
                ),
                (
                    "site_inspection",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.siteinspection",
                        verbose_name="Site d'inspection",
                    ),
                ),
                (
                    "structure_preleveur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.structurepreleveur",
                        verbose_name="Structure préleveur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Prélèvement",
                "verbose_name_plural": "Prélèvements",
                "db_table": "sv_prelevement",
            },
        ),
        migrations.DeleteModel(
            name="PrelevementNonOfficiel",
        ),
        migrations.DeleteModel(
            name="PrelevementOfficiel",
        ),
    ]