# Generated by Django 5.0.8 on 2024-10-22 09:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0024_laboratoireagree_is_active_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="zoneinfestee",
            name="rayon",
            field=models.FloatField(blank=True, null=True, verbose_name="Rayon de la zone infestée"),
        ),
        migrations.AddField(
            model_name="zoneinfestee",
            name="unite_rayon",
            field=models.CharField(
                choices=[("m", "Metre"), ("km", "Kilometre")],
                default="km",
                max_length=2,
                verbose_name="Unité du rayon de la zone infestée",
            ),
        ),
        migrations.AlterField(
            model_name="fichezonedelimitee",
            name="rayon_zone_tampon",
            field=models.FloatField(blank=True, null=True, verbose_name="Rayon tampon réglemantaire ou arbitré"),
        ),
        migrations.AlterField(
            model_name="fichezonedelimitee",
            name="surface_tampon_totale",
            field=models.FloatField(blank=True, null=True, verbose_name="Surface tampon totale"),
        ),
        migrations.AlterField(
            model_name="zoneinfestee",
            name="numero",
            field=models.CharField(blank=True, max_length=50, verbose_name="Numéro de la zone"),
        ),
        migrations.AlterField(
            model_name="zoneinfestee",
            name="surface_infestee_totale",
            field=models.FloatField(blank=True, null=True, verbose_name="Surface infestée totale"),
        ),
    ]
