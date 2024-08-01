# Generated by Django 5.0.3 on 2024-08-01 10:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_document_created_by_document_created_by_structure_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contact",
            name="agent",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to="core.agent"
            ),
        ),
        migrations.AlterField(
            model_name="contact",
            name="structure",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to="core.structure"
            ),
        ),
    ]
