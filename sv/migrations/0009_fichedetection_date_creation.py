# Generated by Django 5.0.3 on 2024-06-12 20:23

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0008_fichedetection_etat"),
    ]

    operations = [
        migrations.AddField(
            model_name="fichedetection",
            name="date_creation",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now, verbose_name="Date de création"
            ),
            preserve_default=False,
        ),
    ]
