# Generated by Django 5.1.7 on 2025-04-03 08:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0025_alter_document_deleted_by_alter_document_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="mimetype",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
