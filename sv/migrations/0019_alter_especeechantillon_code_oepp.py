# Generated by Django 5.0.3 on 2024-09-10 12:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0018_fichedetection_is_deleted"),
    ]

    operations = [
        migrations.AlterField(
            model_name="especeechantillon",
            name="code_oepp",
            field=models.CharField(max_length=100, unique=True, verbose_name="Code OEPP"),
        ),
    ]