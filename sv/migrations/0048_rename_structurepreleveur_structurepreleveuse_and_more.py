# Generated by Django 5.0.8 on 2024-12-10 10:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0047_alter_fichezonedelimitee_unite_surface_tampon_totale"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="StructurePreleveur",
            new_name="StructurePreleveuse",
        ),
        migrations.AlterModelOptions(
            name="structurepreleveuse",
            options={
                "ordering": ["nom"],
                "verbose_name": "Structure préleveuse",
                "verbose_name_plural": "Structures préleveuses",
            },
        ),
        migrations.RenameField(
            model_name="prelevement",
            old_name="structure_preleveur",
            new_name="structure_preleveuse",
        ),
        migrations.AlterField(
            model_name="prelevement",
            name="structure_preleveuse",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.structurepreleveuse",
                verbose_name="Structure préleveuse",
            ),
        ),
    ]