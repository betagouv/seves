# Generated by Django 5.0.8 on 2024-11-14 13:56

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0033_fix_typos_types_exploitant"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="prelevement",
            name="site_inspection",
        ),
    ]