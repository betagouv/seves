# Generated by Django 5.1.6 on 2025-02-18 15:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0024_document_is_infected"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="deleted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="documents_deleted",
                to="core.agent",
            ),
        ),
        migrations.AlterField(
            model_name="document",
            name="description",
            field=models.TextField(blank=True),
        ),
    ]
