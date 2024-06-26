# Generated by Django 5.0.3 on 2024-07-01 14:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_contact_core_contac_email_800caf_idx"),
    ]

    operations = [
        migrations.CreateModel(
            name="StructureHierarchique",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Structure hiérarchique",
                "verbose_name_plural": "Structures hiérarchiques",
            },
        ),
        migrations.AlterField(
            model_name="contact",
            name="complement_fonction",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="contact",
            name="fonction_hierarchique",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="contact",
            name="mobile",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="contact",
            name="telephone",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
