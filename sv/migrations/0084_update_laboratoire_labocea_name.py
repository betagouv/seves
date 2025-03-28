# Generated by Django 5.1.7 on 2025-03-28 13:35

from django.db import migrations


def update_laboratoire_labocea_name(apps, schema_editor):
    laboratoire_model = apps.get_model("sv", "Laboratoire")
    laboratoire_model.objects.filter(nom="Labocéa").update(nom="LDA 22")


def reverse_update_laboratoire_labocea_name(apps, schema_editor):
    laboratoire_model = apps.get_model("sv", "Laboratoire")
    laboratoire_model.objects.filter(nom="LDA 22").update(nom="Labocéa")


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0083_update_dsf_name"),
    ]

    operations = [
        migrations.RunPython(update_laboratoire_labocea_name, reverse_update_laboratoire_labocea_name),
    ]
